#!/usr/bin/env python3

from configparser import ConfigParser

def read_config(path):
    import configparser,os
    config=configparser.ConfigParser()
    config.optionxform = str
    with open(path,'r') as file:
        config.read_file(file)
    dropins=path+'.d'
    if not os.path.exists(dropins):
        return config
    for dropin in os.listdir(dropins):
        with open(dropin,'r') as file:
            config.read_file(file)
    return config

def systemd_escape(where,section_name):
    if where[0]=='/':
        where=where[1:]
    try:
        import subprocess
        return str(subprocess.check_output(['systemd-escape',where,'--suffix',section_name]),'utf-8').strip()
    except:
        where=where.replace('/','-')
        return where+'.'+section_name

def systemd_verify(*paths):
    try:
        import subprocess
        subprocess.run(['systemd-analyze','verify',*paths])
    except:
        print('failed to start systemd-analyze, skipping verification')

def generate_from(name:str,source_unit:ConfigParser,config:ConfigParser):
    generated_units={}
    for section_name in source_unit.sections():
        generated_unit=ConfigParser()
        generated_unit.optionxform = str
        generated_unit.add_section('Unit')
        generated_unit.add_section(section_name)
        generated_unit.add_section('Install')
        for option_name in source_unit.options(section_name):
            value=source_unit.get(section_name,option_name)
            if '.' in option_name:
                config_section_name,option_name=option_name.split('.')
                generated_unit.set(config_section_name,option_name,value)
                continue
            generated_section_name=section_name
            for config_section_name in config.sections():
                if config.has_option(config_section_name,option_name):
                    generated_section_name=config_section_name
                    break
            generated_unit.set(generated_section_name,option_name,value)
        if section_name=='Mount' or section_name=='Automount':
            file_name=systemd_escape(generated_unit.get(section_name,'Where'),section_name.lower())
        else:
            file_name=name+'.'+section_name.lower()
        generated_units[file_name]=generated_unit
    return generated_units

def generate_units(source_dir,dest_dir,config,dry_run=False):
    import os,sys

    if not os.path.exists(source_dir):
        return

    for path in os.listdir(source_dir):
        path=os.path.join(source_dir,path)
        if not path.endswith('.unit'):
            continue
        source_unit=read_config(path)
        source_unit_name=os.path.basename(path).split('.')[0]
        generated_units=generate_from(source_unit_name,source_unit,config)
        for unit_name in generated_units.keys():
            unit_path=os.path.join(dest_dir,unit_name)
            print(unit_path)
            generated_units[unit_name].write(sys.stdout)
            if dry_run:
                continue
            with open(unit_path,'w') as file:
                file.write('#'+__file__+'\n\n')
                generated_units[unit_name].set('Unit','SourcePath',os.path.abspath(path))
                generated_units[unit_name].write(file)
            systemd_verify(unit_path)

def main(args):
    import argparse,os,configparser,sys,traceback

    parser=argparse.ArgumentParser(os.path.basename(__file__),
        description="generate valid systemd units from an extended muti-unit syntax"
    )

    parser.add_argument(
        'normal_unit_dest',
        nargs='?',
        help="output directory for normal units",
    )

    parser.add_argument(
        'early_unit_dest',
        nargs='?',
        help="output directory for early units"
    )

    parser.add_argument(
        'late_unit_dest',
        nargs='?',
        help="output directory for late units"
    )

    parser.add_argument(
        '--normal-unit-source',
        help="input directory/file for normal units"
    )

    parser.add_argument(
        '--early-unit-source',
        help="input directory/file for early units"
    )

    parser.add_argument(
        '--late-unit-source',
        help="input directory/file for late units"
    )

    parser.add_argument(
        '--dry-run',
        help="don't write any files, generate output only",
        action='store_true'
    )

    parser.add_argument(
        '--config',
        help="file containing generator options"
    )

    args=parser.parse_args(args)

    scope=os.environ.get('SYSTEMD_SCOPE')
    if not scope:
        if os.environ.get('UID')=='0':
            scope='system'
        else:
            scope='user'
        os.environ['SYSTEMD_SCOPE']=scope

    if not args.config:
        config_search_path=[os.path.dirname(__file__)+'/generator.conf']
        if scope=='system':
            config_search_path.append('/etc/systemd-multiunit-generator/generator.conf')
        if scope=='user':
            config_search_path.append(os.path.expandvars('$HOME/.config/systemd-multiunit-generator/generator.conf'))
        #config_search_path.reverse()
        for config_path in config_search_path:
            if os.path.isfile(config_path):
                args.config=config_path
                break
        if not args.config:
            print("config file not found",file=sys.stderr)
            exit(1)

    config=read_config(args.config)
    
    if not args.normal_unit_dest:
            args.normal_unit_dest=os.path.expandvars(config.get('GENERATOR','Normal'+scope.capitalize()+'UnitDest'))
            args.early_unit_dest=os.path.expandvars(config.get('GENERATOR','Early'+scope.capitalize()+'UnitDest'))
            args.late_unit_dest=os.path.expandvars(config.get('GENERATOR','Late'+scope.capitalize()+'UnitDest'))

    if not args.early_unit_dest:
        args.early_unit_dest=args.normal_unit_dest
    
    if not args.late_unit_dest:
        args.late_unit_dest=args.normal_unit_dest

    if not (
                args.normal_unit_source or
                args.early_unit_source or
                args.late_unit_source
            ):
        args.normal_unit_source=os.path.expandvars(config.get('GENERATOR','Normal'+scope.capitalize()+'UnitSource'))
        args.early_unit_source=os.path.expandvars(config.get('GENERATOR','Early'+scope.capitalize()+'UnitSource'))
        args.late_unit_source=os.path.expandvars(config.get('GENERATOR','Late'+scope.capitalize()+'UnitSource'))

    if args.early_unit_source and (args.early_unit_dest or args.dry_run):
        generate_units(args.early_unit_source,args.early_unit_dest,config,args.dry_run)
    else:
        print('missing early unit source/dest, skipping')

    if args.normal_unit_source and (args.normal_unit_dest or args.dry_run):
        generate_units(args.normal_unit_source,args.normal_unit_dest,config,args.dry_run)
    else:
        print('missing normal unit source/dest, skipping')

    if args.late_unit_source and (args.late_unit_dest or args.dry_run):
        generate_units(args.late_unit_source,args.late_unit_dest,config,args.dry_run)
    else:
        print('missing late unit source/dest, skipping')

    print('done')

    
if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
