# -*- coding: utf-8 -*-
# Generates the equip regions table found at
# http://wiki.tf/Template:Equip_region_table on the wiki

import re, copy
from vdfparser import VDF

global TF_classes
TF_classes = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy', 'allclass']
verbose = False

itemExceptions = [ # These are keywords which, if present, will make the item ignored.
    '(Scout|Soldier|Pyro|Demo|Heavy|Engineer|Medic|Sniper|Spy)bot Armor',
    'Medicbot Chariot',
    'Sentrybuster',
    'Spine-(Cooling|Tingling|Twisting) Skull', # These are different styles
    'Voodoo-Cursed Soul',

    'Arms Race',
    'Asiafortress Cup',
    'AU Highlander Community League',
    'BETA LAN',
    'DeutschLAN',
    'ESH',
    'ESL',
    'EdgeGamers',
    'ETF2L',
    'FBTF',
    'Florida LAN',
    'GA\'lloween',
    'Gamers Assembly',
    'Gamers With Jobs',
    'InfoShow TF2',
    'LBTF2',
    'OSL.tf',
    'OWL',
    'Ready Steady Pan',
    'RETF2',
    'TF2Connexion',
    'Tumblr Vs Reddit',
    'UGC',
]

def add_region(itemname, TF_classlist, region):
    global regionsDict, TF_classes
    for TF_class in TF_classes:
        if re.search('^'+TF_class, region):
            region = '{{void|'+str(TF_classes.index(TF_class))+'}}'+region
        if re.search('^demo', region):
            region = '{{void|'+str(TF_classes.index('demoman'))+'}}'+region
        if re.search('^medigun', region):
            region = '{{void|'+str(TF_classes.index('medic'))+'}}'+region
        if region == 'none':
            region = '{{void}}none'
    if len(TF_classlist) == len(TF_classes)-1:
        TF_classlist = {'allclass': '1'} # Mimics the style of the actual items_game
    if region not in regionsDict:
        regionsDict[region] = {}
        for TF_class in TF_classes:
            regionsDict[region][TF_class] = []
        if verbose:
            print 'Added region', region
    for TF_class in TF_classlist:
        if itemname not in regionsDict[region][TF_class]:
            regionsDict[region][TF_class].append(itemname)

def add_items():
    schema = VDF()
    prefabs = schema.get_prefabs()
    allitems = dict(schema.get_items(), **prefabs)

    global regionsDict
    for item in allitems:
        item = allitems[item]
        if 'item_name' in item:
            TF_classlist = {}
            if 'used_by_classes' in item:
                TF_classlist = item['used_by_classes']
            itemname = schema.get_localized_item_name(item['item_name'])
            if verbose:
                print 'Processing', itemname
            if 'equip_region' in item:
                if isinstance(item['equip_region'], dict): # Valve are silly and on rare occasions put multiple regions in this field
                    for region in item['equip_region']:
                        if region != 'hat':
                            add_region(itemname, TF_classlist, region.lower())
                else:
                    if item['equip_region'] != 'hat':
                        add_region(itemname, TF_classlist, item['equip_region'].lower())
            elif 'equip_regions' in item:
                regions = item['equip_regions']
                if isinstance(regions, basestring): # Valve are also silly because sometimes they put a single region string here
                    if regions != 'hat':
                        add_region(itemname, TF_classlist, regions.lower())
                else:
                    for region in regions:
                        if region != 'hat':
                            add_region(itemname, TF_classlist, region.lower())
            elif 'prefab' in item:
                if isinstance(item['prefab'], list): # Valve are even sillier because sometimes they put their own name in the prefabs list
                    item['prefab'] = item['prefab'][1]
                if item['prefab'] in prefabs:
                    prefab = prefabs[item['prefab']]
                    if 'used_by_classes' in prefab:
                        TF_classlist.update(prefab['used_by_classes'])
                    if 'equip_region' in prefab and prefab['equip_region'] != 'hat':
                        region = prefab['equip_region']
                        add_region(itemname, TF_classlist, region)
                if item['prefab'] in ['misc', 'valve misc', 'base_misc', 'base_hat', 'ash_remains base_misc']:
                    if verbose:
                        print 'Item', itemname, 'has no equip region. Prefab is:', item['prefab']
                    add_region(itemname, TF_classlist, 'none')

def generate_output():
    global regionsDict, TF_classes
    output = ''
    for regionname, regionitems in regionsDict:
        ### Begin style modifications ###
        # If there are no all-class items, that row is left out.
        # If there are only items for a particular class, only list that class.
        # If there are only items for allclass, only list allclass.
        specificClass = None
        noAllclass = len(regionitems['allclass']) == 0
        length = 0
        for TF_class in TF_classes:
            if re.search(TF_class, regionname):
                specificClass = TF_class
            if re.search('demo', regionname): # Valve are stupid and call things 'demo' when they mean 'demoman'
                specificClass = 'demoman'
            if re.search('medigun', regionname): # Valve are also stupid and call things 'medigun' when they mean 'medic'
                specificClass = 'medic'
            if TF_class != 'allclass':
                length += len(regionitems[TF_class])
        if length == 0: # If there are no items for any class, there must be items for only allclass
            specificClass = 'allclass'

        output += '!'
        if not noAllclass and not specificClass:
            output += ' rowspan="2" |'
        output += ' {{item name|er ' + regionname + '}}'
        blankLines = 0
        for TF_class in TF_classes:
            isAllclass = (TF_class == 'allclass')
            if isAllclass and noAllclass:
                continue
            if specificClass and TF_class != specificClass:
                continue
            regionitems[TF_class].sort(key=lambda s: (s.lower(), s))
            if not specificClass:
                if isAllclass:
                    output += '\n|-'
                else: # This block handles merging multiple blank boxes.
                    if len(regionitems[TF_class]) == 0:
                        blankLines += 1
                    if TF_class == 'spy' or len(regionitems[TF_class]) > 0:
                        output += '\n|'
                        if blankLines > 1:
                            output += ' colspan="%d" |' % blankLines
                        if blankLines != 0 and len(regionitems[TF_class]) > 0:
                            output += '\n|'
                        blankLines = 0

            for n in range(0, len(regionitems[TF_class])):
                item = regionitems[TF_class][n].encode('utf-8')
                if n != 0 and len(regionitems[TF_class]) != 1:
                    output += '<!--\n-->'
                    if not isAllclass and not specificClass:
                        output += '<br />'
                if n == 0:
                    if isAllclass or (specificClass == TF_class):
                        output += '\n| colspan="9" align="center"'
                    output += ' style="font-weight:bold; font-size:0.95em;" | '
                # Items which need custom images go here
                if item == 'Halloween Masks':
                    output += '[[File:Heavy Mask.png|40px]] [[Halloween Masks{{if lang}}|{{item name|Halloween Masks}}]]'
                else:
                    output += '{{item nav link|' + item.decode('utf-8') + '|small=yes}}'
        output += '\n|-\n'
    output += '|}'
    return output

def main():
    global regionsDict
    regionsDict = {}

    if verbose:
        print 'Adding items...'
    add_items()

    # Some input fixes
    for region in regionsDict:
        if 'The Essential Accessories' in regionsDict[region]['scout']:
            regionsDict[region]['scout'].remove('The Essential Accessories')
            regionsDict[region]['scout'].append('Essential Accessories')
        newlist = copy.deepcopy(regionsDict[region])
        for TF_class in TF_classes:
            for item in regionsDict[region][TF_class]:
                for exception in itemExceptions:
                    if re.search(exception, item):
                        newlist[TF_class].remove(item)
                        if verbose:
                            print item, 'discarded, matched filter', exception
                        break
        regionsDict[region] = newlist
    regionsDict = sorted(regionsDict.items())
    if verbose:
        print 'Generating output...'
    return generate_output()

if __name__ == "__main__":
    verbose = True
    f = open('equipregions.txt', 'wb')
    f.write(main().encode('utf-8'))
    f.close()