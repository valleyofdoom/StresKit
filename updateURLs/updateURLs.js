import { readFileSync, writeFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { setOutput } from "@actions/core";

const urls = JSON.parse(readFileSync("../urls.json", { encoding: "utf-8" }));
let commitMessage = "";

async function checkPorteus() {
  try {
    const href =
      "https://ftp.nluug.nl/os/Linux/distr/porteus/x86_64/current/";

    const response = await fetch(href);

    if (!response.ok) {
      throw new Error();
    }

    const html = await response.text();
    const { window } = new JSDOM(html);

    const url = href + window.document.querySelector(`a[href*="OPENBOX"]`).href;

    if (url !== urls.porteus.url) {
      console.log(`New Porteus version found: ${url}`);
      urls.porteus.url = url;
      commitMessage += "- Porteus\n";
    } else {
      console.log("Porteus is up-to-date.");
    }

    return 0;
  } catch {
    console.log("Porteus check has failed.");
    return 1;
  }
}

async function checkPrime95() {
  try {
    let href = "https://www.mersenne.org/download/software/";

    let response = await fetch(href);

    if (!response.ok) {
      throw new Error();
    }

    let html = await response.text();
    let { window } = new JSDOM(html);

    let majorVersion = 0;

    for (const element of window.document.getElementsByTagName("a")) {
      const match = element.href.match(
        new RegExp(`${href.split(".org")[1]}v(\\d+)/`)
      );

      if (match) {
        majorVersion = Math.max(majorVersion, parseInt(match[1], 10));
      }
    }

    href = `${href}v${majorVersion}/`;

    majorVersion = majorVersion.toString().padStart(2, "0");

    await new Promise((r) => {
      setTimeout(r, 100);
    });

    response = await fetch(href);

    if (!response.ok) {
      throw new Error();
    }

    html = await response.text();
    window = new JSDOM(html).window;

    let minorVersion = 0;

    for (const element of window.document.getElementsByTagName("a")) {
      const match = element.href.match(
        new RegExp(`${href.split(".org")[1]}${majorVersion}\\.(\\d+)\\/`)
      );

      if (match) {
        minorVersion = Math.max(minorVersion, parseInt(match[1], 10));
      }
    }

    href = `${href}${majorVersion}.${minorVersion}/`;

    minorVersion = minorVersion.toString().padStart(2, "0");

    await new Promise((r) => {
      setTimeout(r, 100);
    });

    response = await fetch(href);

    if (!response.ok) {
      throw new Error();
    }

    html = await response.text();
    window = new JSDOM(html).window;

    let patchVersion = 0;

    for (const element of window.document.getElementsByTagName("a")) {
      const match = element.href.match(
        new RegExp(
          `${
            href.split(".org")[1]
          }p95v${majorVersion}${minorVersion}b(\\d+)\\.linux64\\.tar\\.gz`
        )
      );

      if (match) {
        patchVersion = Math.max(patchVersion, parseInt(match[1], 10))
          .toString()
          .padStart(2, "0");
      }
    }

    const url = `${href}p95v${majorVersion}${minorVersion}b${patchVersion}.linux64.tar.gz`;

    if (url !== urls.prime95.url) {
      console.log(`New Prime95 version found: ${url}`);
      urls.prime95.url = url;
      commitMessage += "- Prime95\n";
    } else {
      console.log("Prime95 is up-to-date.");
    }

    return 0;
  } catch {
    console.log("Prime95 check has failed.");
    return 1;
  }
}

async function checkYCruncher() {
  try {
    const response = await fetch(
      "https://api.github.com/repos/Mysticial/y-cruncher/releases"
    );

    if (!response.ok) {
      throw new Error();
    }

    const releases = await response.json();

    for (const release of releases) {
      for (const asset of release.assets) {
        const url = asset.browser_download_url;

        if (url.includes("static")) {
          if (url !== urls["y-cruncher"].url) {
            console.log(`New Y-Cruncher version found: ${url}`);
            urls["y-cruncher"].url = url;
            commitMessage += "- Y-Cruncher\n";
          } else {
            console.log("Y-Cruncher is up-to-date.");
          }

          return 0;
        }
      }
    }

    throw new Error();
  } catch {
    console.log("Y-Cruncher check has failed.");
    return 1;
  }
}

async function checkFirestarter() {
  try {
    const response = await fetch(
      "https://api.github.com/repos/tud-zih-energy/FIRESTARTER/releases"
    );

    if (!response.ok) {
      throw new Error();
    }

    const releases = await response.json();

    for (const release of releases) {
      for (const asset of release.assets) {
        const url = asset.browser_download_url;

        if (url.endsWith(".tar.gz")) {
          if (url !== urls.firestarter.url) {
            console.log(`New Firestarter version found: ${url}`);
            urls.firestarter.url = url;
            commitMessage += "- Firestarter\n";
          } else {
            console.log("Firestarter is up-to-date.");
          }

          return 0;
        }
      }
    }

    throw new Error();
  } catch {
    console.log("Firestarter check has failed.");
    return 1;
  }
}

await Promise.all([
  checkPorteus(),
  checkPrime95(),
  checkYCruncher(),
  checkFirestarter(),
]);

writeFileSync("../urls.json", `${JSON.stringify(urls, null, 2)}\n`, {
  encoding: "utf-8",
});

if (commitMessage.length !== 0) {
  commitMessage = `Updated program(s):\n${commitMessage}`;
} else {
  commitMessage = "Update URLs";
}

setOutput("COMMIT_MESSAGE", commitMessage);
