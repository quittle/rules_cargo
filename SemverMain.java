import com.github.zafarkhaja.semver.Version;

import com.vdurmont.semver4j.Semver;
import com.vdurmont.semver4j.Requirement;

import com.google.gson.Gson;

import java.io.File;
import java.io.IOException;

import java.nio.charset.StandardCharsets;

import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Scanner;
import java.util.Set;

public class SemverMain {
    private static void a(final boolean b) {
        a(b, "FAIL!");
    }
    private static void a(final boolean b, final String message) {
        if (!b) {
            throw new AssertionError(message);
        }
    }

    private static void avs(final String version, final String requirement) {
        a(semverMatches(version, requirement),
                String.format("Version: %s Requirement: %s", version, requirement));
    }

    private static class Crate {
        private final String name;
        private final String version;
        private final String[] features;

        public Crate(final String name, final String version) {
            this(name, version, new String[0]);
        }

        public Crate(final String name, final String version, final String[] features) {
            this.name = name;
            this.version = version;
            this.features = features;
        }

        public String getName() {
            return name;
        }

        public String getVersion() {
            return version;
        }

        public String[] getFeatures() {
            return features;
        }

        @Override
        public boolean equals(Object o) {
            if (!(o instanceof Crate)) {
                return false;
            }
            Crate c = (Crate) o;
            return Objects.equals(name, c.name) && Objects.equals(version, c.version);
        }

        @Override
        public int hashCode() {
            return Objects.hash(name, version);
        }
    }

    private static class CargoCrateIndexEntry {
        public static class Dep {
            public String name;
            public String req;
            public String kind;
            public Boolean optional;
            public String[] features;

            @Override
            public String toString() {
                return String.format("Name: %s, Requirement: %s, Kind: %s, Optional: %b", name, req, kind, optional);
            }
        }

        public String name;
        public String vers;
        public Dep[] deps;
    }

    private static boolean semverMatches(final String version, final String requirement) {
        return new Semver(version, Semver.SemverType.LOOSE).satisfies(Requirement.buildNPM(requirement));

        // final String correctedSemverRequirement = requirement.replace(',', '&');
        // return Version.valueOf(version).satisfies(correctedSemverRequirement);
    }

    private static String crateToIndexPath(final String crateName) {
        final String[] pathParts;
        switch (crateName.length()) {
            case 1:
                pathParts = new String[] { "1", crateName };
                break;
            case 2:
                pathParts = new String[] { "2", crateName };
                break;
            case 3:
                pathParts = new String[] { "3", crateName.substring(0, 1), crateName };
                break;
            default:
                pathParts = new String[] { crateName.substring(0, 2), crateName.substring(2, 4), crateName };
        }
        return String.join(File.separator, pathParts);
    }

    private static List<String> fileToLines(final File file) throws IOException {
        final List<String> lines = new LinkedList<>();
        try (final Scanner scanner = new Scanner(file, "UTF-8")) {
            final String line;
            while (scanner.hasNextLine()) {
                lines.add(scanner.nextLine());
            }
        }
        return lines;
    }

    private static <T> Set<T> dup(final Set<T> set, T... extras) {
        final Set<T> newSet = new HashSet<T>(set);
        for (final T extra : extras) {
            newSet.add(extra);
        }
        return newSet;
    }

    private static class Pair<A, B> {
        A first;
        B second;
    }

    private static class DependencyResolutionResult {
        private final Map<Crate, Map<String, Crate>> resolvedDeps;
        private Crate resolvedCrate;

        public DependencyResolutionResult() {
            resolvedDeps = new HashMap<>();
            resolvedCrate = null;
        }

        public void setResolvedCrate(final Crate crate) {
            resolvedCrate = crate;
        }

        public Crate getResolveCrate() {
            return resolvedCrate;
        }

        public void addDependencyResolution(final Crate crate, final Map<String, Crate> deps) {
            resolvedDeps.put(crate, deps);
        }

        public void extendDependencyResolutions(final Map<Crate, Map<String, Crate>> resolvedDeps) {
            this.resolvedDeps.putAll(resolvedDeps);
        }

        public Map<Crate, Map<String, Crate>> getResolvedDeps() {
            return resolvedDeps;
        }
    }

    private static DependencyResolutionResult resolve(final File cargoIndex, final String crateName, final String semverRequirement, final Set<Crate> pickedCrates) throws IOException {
        System.err.println("Finding crate: " + crateName);

        final File cratePath = new File(cargoIndex, crateToIndexPath(crateName));

        final List<String> versions = fileToLines(cratePath);
        Collections.reverse(versions); // Newest versions are appended to the bottom. Use the latest ones first

        // System.err.println("Found this many versions: " + versions.size());
        final Gson gson = new Gson();
        for (final String versionLine : versions) {
            // System.err.println("Checking version: " + versionLine);
            final CargoCrateIndexEntry entry = gson.fromJson(versionLine, CargoCrateIndexEntry.class);
            final String entryVersion = entry.vers;
            if (semverMatches(entryVersion, semverRequirement)) {
                // System.err.println("Found matching version: " + entryVersion);
                final Crate crate = new Crate(crateName, entryVersion);
                if (pickedCrates.contains(crate)) {
                    // System.err.println("Skipping match");
                    continue;
                }

                DependencyResolutionResult result = new DependencyResolutionResult();
                result.setResolvedCrate(crate);
                final Map<String, Crate> resolvedDeps = new HashMap<>();

                // System.err.println("Dep length: " + entry.deps.length);
                boolean abortVersion = false;
                for (final CargoCrateIndexEntry.Dep dep : entry.deps) {
                    if (!"normal".equals(dep.kind) || dep.optional) {
                        continue;
                    }
                    // System.err.println("Investiging: " + dep);
                    DependencyResolutionResult resolvedCrates = resolve(cargoIndex, dep.name, dep.req, dup(pickedCrates, crate));
                    if (resolvedCrates == null) {
                        abortVersion = true;
                        break;
                    } else {
                        // System.err.println("Itsa match!");
                        assert dep.name.equals(resolvedCrates.getResolveCrate());
                        result.extendDependencyResolutions(resolvedCrates.getResolvedDeps());
                        resolvedDeps.put(dep.name, resolvedCrates.getResolveCrate());
                        // result.getResolvedDeps().putAll(resolvedCrates.getResolvedDeps());
                    }
                }
                if (!abortVersion) {
                    result.getResolvedDeps().put(crate, resolvedDeps);
                    // System.err.println("Not aborting!");
                    return result;
                }
            }
        }
        System.err.println("Unable to resolve dependencies");
        return null;

        /*

                # Skip it if we already have it to avoid a cyclical dependency
                if key in dep_set:
                    eprint("cycle found. Depset: " + str(dep_set))
                    continue

                deps = version_blob['deps']
                ret = { key: { dep['name']: dep for dep in deps } }
                abort_version = False
                for dep in deps:
                    dep_name = dep['name']
                    if dep['kind'] != 'normal' or dep['optional']:
                        continue
                    resolved_dep, resolved_version = resolve(index, dep_name, dep['req'], dep_set | set([key]))
                    if resolved_dep is None:
                        eprint('Unable to resolve dep: ' + json.dumps(dep))
                        # This is fine. maybe we can work with the next version
                        abort_version = True
                        break
                    else:
                        # make this a name-keyed dict instead of a list
                        ret[key][dep_name]['__resolved_version'] = resolved_version
                        ret.update(resolved_dep)
                # One of the dependencies couldn't be resolved, move on to the next
                if not abort_version:
                    return ret, version
    eprint('Unable to find ' + crate + ' version ' + requirements)
    return None
         */
    }

    public static void main(final String[] args) throws IOException {
        avs("1.0.0", "^1");
        avs("0.0.1", "*");
        avs("2.0.3-alpha1", "*");
        avs("1.0.0", "*");
        avs("1.0.0", "^1");
        avs("1.0.0", "^1.0");
        avs("1.4.0", "^1.2.3");
        // avs("2.5.0", ">=2.5,<2.30,>1,^2.5,2.5");
        // avs("2.5.0", "= 2.5");
        avs("2.5.0", "2.5.0");
        avs("0.11.1", "^0.11.0-rc.2");

        if (args.length != 3) {
            throw new IllegalArgumentException(String.format("3 arguments expected but received %d. {crateName} {crateVersion} {cargoIndexLoc}", args.length));
        }

        final String rootCrateName = args[0];
        final String rootCrateVersion = args[1];
        final String cargoIndexLoc = args[2];

        final File cargoIndexRoot = new File(cargoIndexLoc);

        final DependencyResolutionResult resolvedCrates = resolve(cargoIndexRoot, rootCrateName, rootCrateVersion, new HashSet<Crate>());
        System.err.println("# of resolved crates: " + resolvedCrates.getResolvedDeps().size());

        resolvedCrates.getResolvedDeps().forEach((crate, deps) -> {
            System.out.print(crate.name + " " + crate.version + " ");
            deps.forEach((name, dep) -> {
                System.out.print(dep.name + " " + dep.version + " " + String.join(":", dep.features) + " ");
            });
            System.out.println();
        });
    }
}