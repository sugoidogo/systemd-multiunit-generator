# Systemd MultiUnit Generator
this is a prototype systemd unit generator that allows defining multiple related units in a single file

# Usage
because this is a python script, you'll need to have python 3 installed. You can use `systemd-multiunit-genconf.py` to generate the default config file from your system's `man systemd.unit` output, or you can use the pre-generated `generator.conf`. Once you have your config, place it at `/etc/systemd-multiunit-generator/generator.conf` and place `systemd-multiunit-generator.py` under `/etc/systemd/system-generators/` and make sure it's executable. You can place your multiunits under `/etc/systemd-multiunit-generator/system/` with the `.unit` file extention, and it will also load drop-ins from `*.unit.d/*`.

Example unit(s) can be found here in the `test_source` directory.