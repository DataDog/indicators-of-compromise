## Indicators of compromise for the Shai Hulud 2.0 campaign

This repository contains lists of compromised legitimate npm packages as part of the "Shai Hulud 2.0" worm.

### Datadog IOCs

[shai-hulud-2.0.csv](shai-hulud-2.0.csv) contains a non-comprehensive list of npm packages that we have manually confirmed and witnessed were backdoored in the Shai Hulud 2.0 campaign.

Format: one tuple (package_name, package_version) per line. If multiple versions of a single package were backdoored, each version appears on a separate line.

Last updated: 2025-11-24.

## Consolidated vendor IOCs

As part of this incident, a number of vendors reported on their IOCs. However, defenders need consolidated lists spanning multiple vendors in order to achieve satisfying coverage.

[consolidated_iocs.csv](consolidated_iocs.csv) contains deduplicated IOCs from the following research blog posts:

- https://www.koi.ai/incident/live-updates-sha1-hulud-the-second-coming-hundred-npm-packages-compromised
- https://www.stepsecurity.io/blog/sha1-hulud-the-second-coming-zapier-ens-domains-and-other-prominent-npm-packages-compromised
- https://www.aikido.dev/blog/shai-hulud-strikes-again-hitting-zapier-ensdomains
- https://www.wiz.io/blog/shai-hulud-2-0-ongoing-supply-chain-attack
- https://www.reversinglabs.com/blog/another-shai-hulud-npm-worm-is-spreading-heres-what-you-need-to-know   
- https://helixguard.ai/blog/malicious-sha1hulud-2025-11-24

*Last retrieved: 2025-11-26 at 1:30pm UTC*

We have ignored vendors reporting on compromised packages without providing package versions.

Format: If multiple versions of a single package were backdoored, versions are aggregated. This means that each package name is unique in the CSV file, and each vendor is included in the vendors list having reported on it if they reported on at least one version.

We have manually removed the followed IOCs which we deem to be false positives:

```
package_name,package_versions,vendors
cbre-flow-common,"99.2.0, 99.3.0, 99.4.0, 99.5.0, 99.6.0",helixguard
@elsedev/react-csr-sdk,1.0.17,helixguard
utilitas,"2000.3.10, 2000.3.4, 2000.3.5",helixguard
```