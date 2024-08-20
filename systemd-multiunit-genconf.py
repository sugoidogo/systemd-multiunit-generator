#!/usr/bin/env python3

def typegen():
    import subprocess,re

    man=subprocess.check_output(['man','systemd.unit']).decode().splitlines(False)
    option=re.compile("^\\s*\\w+=(, \\w+=)*$")
    section=re.compile('^\\s*\\[[A-Z]+\\]')
    generics={}
    currentSection=None
    match=None

    for line in man:
        if line=='EXAMPLES':
            break
        if match := option.match(line):
            generics[currentSection].extend(match.group(0).strip().split(', '))
            continue
        if match := section.match(line):
            currentSection=match.group(0).strip()
            if currentSection not in generics:
                generics[currentSection]=[]

    return generics

if __name__ == "__main__":
    print('''[Generator]
NormalSystemUnitDest=/run/systemd/generator
EarlySystemUnitDest=/run/systemd/generator.early
LateSystemUnitDest=/run/systemd/generator.late

NormalUserUnitDest=$XDG_RUNTIME_DIR/systemd/generator
EarlyUserUnitDest=$XDG_RUNTIME_DIR/systemd/generator.early
LateUserUnitDest=$XDG_RUNTIME_DIR/systemd/generator.late

NormalSystemUnitSource=/etc/systemd-multiunit-generator/$SYSTEMD_SCOPE
EarlySystemUnitSource=/etc/systemd-multiunit-generator/$SYSTEMD_SCOPE.early
LateSystemUnitSource=/etc/systemd-multiunit-generator/$SYSTEMD_SCOPE.late

NormalUserUnitSource=$HOME/.config/systemd-multiunit-generator/$SYSTEMD_SCOPE
EarlyUserUnitSource=$HOME/.config/systemd-multiunit-generator/$SYSTEMD_SCOPE.early
LateUserUnitSource=$HOME/.config/systemd-multiunit-generator/$SYSTEMD_SCOPE.late''')
    types=typegen()
    for sectionName in types.keys():
        print("\n["+sectionName[1:-1].lower().capitalize()+']')
        for optionName in types[sectionName]:
            print(optionName)

