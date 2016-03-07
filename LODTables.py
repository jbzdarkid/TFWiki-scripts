import os
from vdfparser import VDF
import re
verbose = False
rootdir = "/Users/joe/Github/TFWiki-scripts/decompiled/"
TF_classes = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy', 'multi-class', 'all classes']
item_slots = ['primary', 'secondary', 'melee', 'pda', 'pda2', 'building', 'cosmetic', 'building2', 'class']
max = {TF_class:0 for TF_class in TF_classes} # 2.7+, sorry :(
max['Weapons'] = 0
max['Building2'] = 0
max['Classes'] = 0

def gen_allitems():
	schema = VDF()
	items = schema.get_items()
	prefabs = schema.get_prefabs()
	allitems = dict(items, **prefabs)

	# Fix for some broken weapons
	for key in allitems:
		item = allitems[key]
		if 'prefab' in item and 'extra_wearable' not in item:
			prefab = item['prefab']
			if prefab[0] == 'valve': # Valve are silly and occasionally put their name into the prefabs
				prefab = prefab[1]
			prefab = prefab.split(' ')[-1]
			if prefab[:7] == 'weapon_' or prefab in ['holy_mackerel', 'axtinguisher', 'buff_banner', 'sandvich', 'ubersaw', 'frontier_justice', 'huntsman', 'ambassador']:
				if prefab == 'weapon_shotgun':
					prefab = 'weapon_shotgun_multiclass'
				if prefab == 'weapon_melee_allclass':
					print 'Skipping', key
					continue
				item['item_slot'] = prefabs[prefab]['item_slot']
				item['used_by_classes'] = prefabs[prefab]['used_by_classes']

	# Some hard-coded additions. This _vaguely_ mimics the schema's true format.
	buildings = {
		'Sentry Gun Level 1': {
			'model_world': 'models/buildings/sentry1.mdl',
			'item_name': '#TF_Object_Sentry',
			'level': '1',
		},
		'Sentry Gun Level 2': {
			'model_world': 'models/buildings/sentry2_optimized.mdl',
			'item_name': '#TF_Object_Sentry',
			'level': '2',
		},
		'Sentry Gun Level 3': {
			'model_world': 'models/buildings/sentry3_optimized.mdl',
			'item_name': '#TF_Object_Sentry',
			'level': '3',
		},
		'Dispenser Level 1': {
			'model_world': 'models/buildings/dispenser_toolbox.mdl',
			'item_name': '#TF_Object_Dispenser',
			'level': '1',
		},
		'Dispenser Level 2': {
			'model_world': 'models/buildings/dispenser_lvl2.mdl',
			'item_name': '#TF_Object_Dispenser',
			'level': '2',
		},
		'Dispenser Level 3': {
			'model_world': 'models/buildings/dispenser_lvl3.mdl',
			'item_name': '#TF_Object_Dispenser',
			'level': '3',
		},
		'Teleporter': {
			'model_world': 'models/buildings/teleporter.mdl',
			'item_name': '#TF_Object_Tele',
		}
	}
	for building in buildings:
		buildings[building]['used_by_classes'] = {'engineer': '1'},
		buildings[building]['item_slot'] = 'building2'
	allitems.update(buildings)
	for TF_class in TF_classes:
		allitems[TF_class.title()] = {
			'model_world': 'models/player/%s.mdl' % TF_class,
			'model_player': 'models/player/%s_morphs_high.mdl' % TF_class,
			'item_name': '#TF_class_Name_%s' % TF_class,
			'used_by_classes': {TF_class: '1'},
			'item_slot': 'class'
		}
	# Exceptions to exceptions
	allitems['Demoman']['model_player'] = 'models/player/demo.mdl'
	allitems['Demoman']['model_world'] = 'models/player/demo_morphs_high.mdl'
	allitems['Heavy']['item_name'] = '#TF_class_Name_HWGuy'
	return allitems

# Generates a map of model name (i.e. c_rift_fire_mace) to weapon name (i.e. Sun On-A-Stick)
def gen_modelmap(allitems):
	modelmap = {}
	schema = VDF()
	for key in allitems:
		item = allitems[key]

		# Get model name.
		if 'model_world' in item:
			modelmap[item['model_world']] = [key]
		if 'model_player' in item:
			modelmap[item['model_player']] = [key]
		if 'model_player_per_class' in item:
			for model in item['model_player_per_class'].values():
				modelmap[model] = [key]
		if 'visuals' in item and 'styles' in item['visuals']:
			for style in item['visuals']['styles'].values():
				if 'model_player' in style:
					if 'name' not in style:
						pass
						# modelmap[modelname] = [key, {
						# 	'coin_summer2015_gravel': 'Gun Mettle Campaign Coin (Gravel)',
						# 	'coin_summer2015_bronze': 'Gun Mettle Campaign Coin (Bronze)',
						# 	'coin_summer2015_silver': 'Gun Mettle Campaign Coin (Silver)',
						# 	'coin_summer2015_gold': 'Gun Mettle Campaign Coin (Gold)',
						# 	'stamp_winter2016': 'Tough Break Stamp',
						# }[modelname]]
					else:
						modelmap[style['model_player']] = [key, style['name']]
				if 'model_player_per_class' in style:
					for model in item['model_player_per_class'].values():
						modelmap[model] = [key, style['name']]

	# Convert the model name to a readable string. This is using .keys() and .values() because we change the dict during iteration.
	for (key, value) in zip(modelmap.keys(), modelmap.values()):
		del modelmap[key]
		propername = schema.get_localized_item_name(allitems[value[0]]['item_name'])
		if propername == 'The Essential Accessories':
			propername = 'Essential Accessories'
		elif propername == 'Teleporter':
			propername = 'Teleporters'
		if len(value) == 2: # Styles add-in
			style = schema.get_localized_item_name(value[1])
			if style:
				propername += '|style='+style
		if 'level' in allitems[value[0]]: # Hack for engineer buildings
			print 137
			propername += '|level='+allitems[value[0]]['level']
		if 'vision_filter_flags' in allitems[value[0]]: # Romevision bot armor
			continue
		modelname = re.search('/([a-zA-Z0-9_]*)\.mdl', key)
		if modelname:
			modelmap[modelname.group(1)] = [value[0], propername]

	return modelmap

def gen_files(modelmap):
	for root, subFolders, files in os.walk(rootdir):
		for file in files:
			if file[-4:] != '.smd':
				continue
			if file[-11:] == 'physics.smd':
				continue
			if file[-13:] == 'bodygroup.smd':
				continue
			if file == 'idle.smd':
				continue
			filename = os.path.join(root, file) # Save the name before we modify the file variable
			file = file[:-4] # Cuts .smd
			if file[-13:] == 'reference':
				modelname = file[:-14]
			else:
				if file[-5:-1] == '_lod':
					file = file[:-5]
				if file[-10:] == '_reference':
					file = file[:-10]
				if file[-5:] == 'shell':
					continue
				if file[-9:] == 'shell_xms':
					continue
				if file == 'c_flaregun_pyro_c_flaregun_shell' or file == 'c_xms_flaregun_c_flaregun_shell_xms':
					print file[-5:]
					continue
				parts = file.split('_')
				modelname = parts[0]
				# Converts 'c_backburner_c_flamethrower' -> 'c_backburner'
				for p in range(1, len(parts)):
					if parts[p] == parts[0]:
						for q in range(1, p):
							modelname += '_'+parts[q]
						break
					if p == len(parts)-1:
						modelname = file
			if modelname not in modelmap:
				continue
			yield (filename, modelname)

def gen_data(allitems, modelmap):
	data = {TF_class:[{} for _ in item_slots] for TF_class in TF_classes}
	for (filename, modelname) in gen_files(modelmap):
		f = open(filename, 'rb').read() # We open the file (and read it) because we need a count of the number of lines.
		lines = f.split('\r\n')
		count = 0
		for i in range(len(lines)):
			if lines[i] == 'triangles':
				count = (len(lines) - i - 3)/4
				break
		if count == 0: # Non-models don't have 'triangles' in them, so we ignore them
			continue
		[name, propername] = modelmap[modelname]
		if 'used_by_classes' not in allitems[name]:
			continue
		usedby = allitems[name]['used_by_classes']
		if len(usedby) == 1:
			TF_class = usedby.keys()[0]
		elif len(usedby) == 9:
			TF_class = 'all classes'
		else:
			TF_class = 'multi-class'
		if 'item_slot' in allitems[name]: # Default, used for weapons and new cosmetic listings.
			slot = allitems[name]['item_slot']
		elif 'prefab' in allitems[name]:
			slot = 'cosmetic'
		if slot in ['misc', 'head']: # Old cosmetic listings
			slot = 'cosmetic'
		if slot not in item_slots:
			continue
		item_slot = item_slots.index(slot)
		# Primary, secondary, melee, pda, pda2, building
		if item_slot < 6 and max['Weapons'] < count:
			max['Weapons'] = count
		# Cosmetic
		elif item_slot == 6 and max[TF_class] < count:
			max[TF_class] = count
		# Building2
		elif item_slot == 7 and max['Building2'] < count:
			print 227
			max['Building2'] = count
		# Class
		elif item_slot == 8 and max['Classes'] < count:
			max['Classes'] = count

		# Item doesn't exist
		if propername not in data[TF_class][item_slot]:
			data[TF_class][item_slot][propername] = [count, count]
		# Item exists, found new minimum LOD
		elif data[TF_class][item_slot][propername][0] < count:
			data[TF_class][item_slot][propername][0] = count
		# Item exists, found new maximum LOD
		elif data[TF_class][item_slot][propername][1] > count:
			data[TF_class][item_slot][propername][1] = count
	return data

def get_weapons(data):
	output = ''
	for TF_class in TF_classes:
		count = 0
		for j in range(6):
			count += len(data[TF_class][j])
		output += '|rowspan="%d" data-sort-value="%d"| {{Class link|%s}}\n' % (count, TF_classes.index(TF_class), TF_class)
		for j in range(6):
			if len(data[TF_class][j]) != 0:
				output += '|rowspan="%d" data-sort-value="%d"|{{Item name|%s}}\n' % (len(data[TF_class][j]), j, item_slots[j])
			for k in sorted(data[TF_class][j].keys()):
				output += '{{LODTable/core|max=%d|%s|%d' % (max['Weapons'], k.encode('utf-8'), data[TF_class][j][k][0])
				if data[TF_class][j][k][0] != data[TF_class][j][k][1]:
					output += '|%d' % data[TF_class][j][k][1]
				output += '}}\n'
	return output

def get_cosmetics(data, TF_class):
	output = ''
	for k in sorted(data[TF_class][6].keys()):
		output += '{{LODTable/core|max=%d|%s|%d' % (max[TF_class], k.encode('utf-8'), data[TF_class][6][k][0])
		if data[TF_class][6][k][0] != data[TF_class][6][k][1]:
			output += '|%d' % data[TF_class][6][k][1]
		output += '}}\n'
	return output

def get_buildings(data):
	output = ''
	for TF_class in TF_classes:
		print data[TF_class][7]
		if len(data[TF_class][7]) == 0:
			continue
		output += '|rowspan="%d" data-sort-value="%d"| {{Class link|%s}}\n' % (len(data[TF_class][7]), TF_classes.index(TF_class), TF_class)
		for k in sorted(data[TF_class][7].keys()):
			output += '{{LODTable/core|max=%d|%s|%d' % (max['Buildings2'], k.encode('utf-8'), data[TF_class][7][k][0])
			if data[TF_class][7][k][0] != data[TF_class][7][k][1]:
				output += '|%d' % data[TF_class][7][k][1]
			output += '}}\n'
	return output

def get_classes(data):
	output = ''
	for TF_class in TF_classes:
		if len(data[TF_class][8]) == 0:
			continue
		for k in sorted(data[TF_class][8].keys()):
			output += '{{LODTable/core|max=%d|%s|%d' % (max['Classes'], k.encode('utf-8'), data[TF_class][8][k][0])
			if data[TF_class][8][k][0] != data[TF_class][8][k][1]:
				output += '|%d' % data[TF_class][8][k][1]
			output += '}}\n'
		output += '|}'
	return output

def main():
	allitems = gen_allitems()
	if verbose:
		print 'Found %d items' % len(allitems)
	modelmap = gen_modelmap(allitems)
	if verbose:
		print 'Generated model map'
	data = gen_data(allitems, modelmap)
	if verbose:
		print 'Done counting triangles'

	output = ''
	output += '''== {{Item name|Weapons}} ==
{| class="wikitable sortable grid"
! class="header" width="10%" | {{Common string|Class}}
! class="header" width="7%" | {{Common string|LOD Slot}}
! class="header" width="17%" | {{Item name|Item}}
! class="header" width="32%" | {{Common string|LOD High Quality}}
! class="header" width="32%" | {{Common string|LOD Low Quality}}
! class="header" width="2%" | {{Common string|LOD Efficiency}}
|-\n'''
	output += get_weapons(data)
	output += '''|}

== {{Item name|Cosmetics}} ==
{| style="width: 30%; text-align: center"
| style="width: 20%" | {{Common string|LOD Key}}
| style="background:#93AECF; width: 40%" | {{Common string|LOD Unoptimized}}
| style="background:#F3A957; width: 40%" | {{Common string|LOD Optimized}}
|}
'''
	for TF_class in TF_classes:
		output += '=== {{Class name|%s}} ===' % TF_class
		output += '''
{| class="wikitable sortable grid collapsible collapsed"
! class="header" width="20%" | {{Item name|Item}}
! class="header" width="38%" | {{Common string|LOD High Quality}}
! class="header" width="38%" | {{Common string|LOD Low Quality}}
! class="header" width="2%" | {{Common string|LOD Efficiency}}
|-\n'''
		output += get_cosmetics(data, TF_class)
		output += '|}\n'
	output += '''
== {{Item name|Buildings}} ==
{| style="width: 30%; text-align: center"
| style="width: 20%" | {{Common string|LOD Key}}
| style="background:#93AECF; width: 40%" | {{Common string|LOD Unoptimized}}
| style="background:#F3A957; width: 40%" | {{Common string|LOD Optimized}}
|}

{| class="wikitable sortable grid"
! class="header" width="10%" | {{Common string|Class}}
! class="header" width="18%" | {{Item name|Item}}
! class="header" width="35%" | {{Common string|LOD High Quality}}
! class="header" width="35%" | {{Common string|LOD Low Quality}}
! class="header" width="2%" | {{Common string|LOD Efficiency}}
|-\n'''
	output += get_buildings(data)
	output += '''|}

== {{Common string|Classes}} ==
{| class="wikitable sortable grid"
! class="header" width="10%" | {{Common string|Class}}
! class="header" width="18%" | {{Item name|Item}}
! class="header" width="35%" | {{Common string|LOD High Quality}}
! class="header" width="35%" | {{Common string|LOD Low Quality}}
! class="header" width="2%" | {{Common string|LOD Efficiency}}
|-\n'''
	output += get_classes(data)
	output += '|}'
	return output

if __name__ == '__main__':
	verbose = True
	f = open('LODTables.txt', 'wb')
	f.write(main())
	print 'Article written to LODTables.txt'
	f.close()
