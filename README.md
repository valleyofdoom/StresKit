# StresKit

[![Downloads](https://img.shields.io/github/downloads/valleyofdoom/StresKit/total.svg)](https://github.com/valleyofdoom/StresKit/releases)

Lightweight bootable ISO based on [Porteus](https://www.porteus.org) containing a compendium of stress-testing related tools and utilities.

## Setup

1. Download the latest [StresKit](https://github.com/valleyofdoom/StresKit/releases) ISO and burn it to a USB with [Rufus](https://rufus.ie/en) then boot to it through UEFI. [Ventoy](https://www.ventoy.net/en/index.html) (use grub2 mode if normal mode doesn't work) is another popular option
2. The login username is ``guest`` and the password is ``guest``
3. After logging in, you can use the tools packaged in StresKit. See the [Usage](#usage) section for the available tools

## Usage

- [Toggling Mitigations](#toggling-mitigations)
- [Switch TTY](#switch-tty)
- [Sensors](#sensors)
- [Viewing Large Outputs](#viewing-large-outputs)
- [Accessing Local Storage](#accessing-local-storage)
- [Linpack](#linpack)
- [Prime95](#prime95)
- [y-cruncher](#y-cruncher)
- [Intel Memory Latency Checker (Intel MLC)](#intel-memory-latency-checker-intel-mlc)
- [stressapptest (GSAT)](#stressapptest-gsat)
- [s-tui](#s-tui)
- [FIRESTARTER](#firestarter)

### Toggling Mitigations

By default, mitigations are disabled. To enable them, remove the line that disables mitigations in [porteus.cfg](/porteus/boot/syslinux/porteus.cfg) after mounting the ISO to a USB (or build a new ISO with the modified config). Enabling mitigations may provide a performance uplift for certain systems ([1](https://www.phoronix.com/review/amd-zen4-spectrev2)).

### Display StresKit Help Message

Type ``skhelp`` to display the [pre-login help message](/porteus/porteus/rootcopy/etc/issue) for a brief overview of the available commands.

### Switch TTY

In cases where you need to multitask but can't interact with the main terminal such as wanting to view sensors while a stress-test is running, you can switch to another *virtual terminal* by pressing ``Ctrl+Alt+F2`` and complete your tasks on there. Switch back to TTY 1 by pressing ``Ctrl+Alt+F1``.

### Sensors

Type ``watch sensors`` to view sensors. [s-tui](#s-tui) is also an available option. You can view sensors while a stress-test is running by [switching to another TTY](#switch-tty).

To monitor a specific sensor, specify the name of the sensor in the command ``watch sensors <sensor_name>``. See example below.

Output of ``watch sensors``:

```ba
nouveau-pci-0100
Adapter: PCI adapter
fan1:           0RPM
temp1:        +33.0°C (high = +95.0°C, hyst = +3.0°C)
                      (crit = +105.0°C, hyst = +5.0°C)
                      (emerg = +135.0°C, hyst = +5.0°C)

acpitz-acpi-0
Adapter: ACPI interface
temp1:        +27.8°C (crit = +119.0°C)

coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +35.0°C (high = +101.0°C, crit = +115.0°C)
Core 0:        +30.0°C (high = +101.0°C, crit = +115.0°C)
Core 1:        +30.0°C (high = +101.0°C, crit = +115.0°C)
Core 2:        +34.0°C (high = +101.0°C, crit = +115.0°C)
Core 3:        +28.0°C (high = +101.0°C, crit = +115.0°C)
Core 4:        +28.0°C (high = +101.0°C, crit = +115.0°C)
Core 5:        +28.0°C (high = +101.0°C, crit = +115.0°C)
Core 6:        +35.0°C (high = +101.0°C, crit = +115.0°C)
Core 7:        +27.0°C (high = +101.0°C, crit = +115.0°C)

nume-pci-0400
Adapter: PCI adapter
Composite:    +28.9°C (low  = -273.1°C, high = +81.8°C)
                      (crit = +84.8°C)

Sensor 1:     +28.9°C (low = -273.1°C, high +65261.8°C)
Sensor 2:     +35.9°C (low = -273.1°C, high = +65261.8°C)
```

To only view ``coretemp-isa-0000``, you would type:

```bash
watch sensors coretemp-isa-0000
```

Another useful command can be displaying the CPU frequency with the command below:

```bash
watch "sensors && cat /proc/cpuinfo | grep MHz"
```

### Viewing Large Outputs

Scrolling in Porteus is a bit tedious. For this reason, you can write stdout to a file while viewing the output simultaneously with the ``tee`` command. This also allows you to back up the output on a USB drive if needed which can be useful for other purposes such as saving them for later or comparing results.

```bash
<command> | tee -a output.txt
```

Learn the basic syntax of ``vi`` by watching [this video](https://www.youtube.com/watch?v=vo2FXvPkcEA). Use ``vi output.txt`` to view the ``output.txt`` file at any given time.

### Accessing Local Storage

Sometimes you may want to access local storage whether it be the USB or your computer's drive.

To identify mounted devices, type:

```bash
ls /mnt/*
```

You can ``ls`` each of them to identify which is the desired storage device if the name isn't obvious.

### [Linpack](https://en.wikipedia.org/wiki/LINPACK_benchmarks)

Usage:

```
linpack.sh [-m <gb>] [-s <samples>]
```

- ``-m`` is the memory size in gigabytes. If not specified, free memory minus 100mb will be used
- ``-s`` is the number of trials to run. If not specified, 100 trials will be executed

### [Prime95](https://www.mersenne.org/download)

Usage:

```bash
mprime
```

### [y-cruncher](http://www.numberworld.org/y-cruncher)

Usage:

```bash
y-cruncher
```

### [Intel Memory Latency Checker (Intel MLC)](https://www.intel.com/content/www/us/en/developer/articles/tool/intelr-memory-latency-checker.html)

Usage:

```bash
mlc
```

### [stressapptest (GSAT)](https://github.com/stressapptest/stressapptest)

Usage:

```bash
stressapptest
```

### [s-tui](https://github.com/amanusk/s-tui)

Usage:

```bash
s-tui
```

### [FIRESTARTER](https://github.com/tud-zih-energy/FIRESTARTER)

Usage:

```bash
FIRESTARTER
```

## Building

The ``build.py`` script can be used to build the ISO. It is designed to run on [ubuntu-latest](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#choosing-github-hosted-runners) for GitHub actions, but you can use a Linux distro of your choice.

```bash
git clone https://github.com/valleyofdoom/StresKit.git
cd StresKit/
python build.py
```
