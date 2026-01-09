import hashlib
import random

from windbot_utils import *

class DictionaryUpdater:
    def __init__(self):
        self.subpageTemplateLang = """{{#switch:{{{lang|{{SUBPAGENAME}}}}}|%options%}}"""
        self.subpageTemplateParam = """{{#switch:{{{1|}}}|%options%}}"""
        self.invalidParamError = """<span class="error">Error: invalid param.</span>[[Category:ERROR]]"""
        self.invalidKeyNameCharacters = """#<>[]{}"""
        self.subpageTemplateID = """%string%"""
        self.partialUpdateThreshold = 750 # Update SyncData every n edits
        self.dictionaries = {
            # u'Template:Dictionary/items': { # Dictionary page
            #     'name': 'items', # Dictionary name (used for categorizing)
            #     'sync': 'Template:Dictionary/items/Special:SyncData' # Page holding last sync data
            # },
            u'Template:Dictionary/items2': { # Dictionary page
                'name': 'items2', # Dictionary name (used for categorizing)
                'overridePath': 'Template:Dictionary/items',
                'sync': 'Template:Dictionary/items2/Special:SyncData' # Page holding last sync data
            },
            # u'Template:Dictionary/common strings': { # Warning: no underscore
            #     'name': 'common strings',
            #     'sync': 'Template:Dictionary/common strings/Special:SyncData'
            # },
            # u'Template:Dictionary/classes': {
            #     'name': 'classes',
            #     'sync': 'Template:Dictionary/classes/Special:SyncData'
            # },
            # u'Template:Dictionary/demonstrations': {
            #     'name': 'demonstrations',
            #     'sync': 'Template:Dictionary/demonstrations/Special:SyncData'
            # },
            # u'Template:Dictionary/price': {
            #     'name': 'price',
            #     'sync': 'Template:Dictionary/price/Special:SyncData',
            #     'allTemplate': '{{{{{template|item price/fmt}}}|%options%|tt={{{tt|yes}}}}}'
            # },
            # u'Template:Dictionary/merchandise': {
            #     'name': 'merchandise',
            #     'sync': 'Template:Dictionary/merchandise/Special:SyncData'
            # },
            # u'Template:Dictionary/decorated': {
            #     'name': 'decorated',
            #     'sync': 'Template:Dictionary/decorated/Special:SyncData'
            # },
            # u'Template:Dictionary/descriptions': {
            #     'name': 'descriptions',
            #     'sync': 'Template:Dictionary/descriptions/Special:SyncData'
            # },
            # u'Template:Dictionary/dyk': {
            #     'name': 'dyk',
            #     'sync': 'Template:Dictionary/dyk/Special:SyncData'
            # },
            # u'Template:Dictionary/tournament medals': {
            #     'name': 'tournament medals',
            #     'sync': 'Template:Dictionary/tournament medals/Special:SyncData'
            # },
            # u'Template:Dictionary/attributes': {
            #     'name': 'attributes',
            #     'sync': 'Template:Dictionary/attributes/Special:SyncData'
            # },
            # u'Template:Dictionary/steam ids': {
            #     'name': 'steam ids',
            #     'sync': 'Template:Dictionary/steam ids/Special:SyncData'
            # },
            # u'Template:Dictionary/tips': {
            #     'name': 'tips',
            #     'sync': 'Template:Dictionary/tips/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/scout': {
            #     'name': 'achievements/scout',
            #     'sync': 'Template:Dictionary/achievements/scout/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/soldier': {
            #     'name': 'achievements/soldier',
            #     'sync': 'Template:Dictionary/achievements/soldier/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/pyro': {
            #     'name': 'achievements/pyro',
            #     'sync': 'Template:Dictionary/achievements/pyro/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/demoman': {
            #     'name': 'achievements/demoman',
            #     'sync': 'Template:Dictionary/achievements/demoman/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/heavy': {
            #     'name': 'achievements/heavy',
            #     'sync': 'Template:Dictionary/achievements/heavy/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/engineer': {
            #     'name': 'achievements/engineer',
            #     'sync': 'Template:Dictionary/achievements/engineer/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/medic': {
            #     'name': 'achievements/medic',
            #     'sync': 'Template:Dictionary/achievements/medic/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/sniper': {
            #     'name': 'achievements/sniper',
            #     'sync': 'Template:Dictionary/achievements/sniper/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/spy': {
            #     'name': 'achievements/spy',
            #     'sync': 'Template:Dictionary/achievements/spy/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/general': {
            #     'name': 'achievements/general',
            #     'sync': 'Template:Dictionary/achievements/general/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/halloween': {
            #     'name': 'achievements/halloween',
            #     'sync': 'Template:Dictionary/achievements/halloween/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/treasure hunt': {
            #     'name': 'achievements/treasure hunt',
            #     'sync': 'Template:Dictionary/achievements/treasure hunt/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/replay': {
            #     'name': 'achievements/replay',
            #     'sync': 'Template:Dictionary/achievements/replay/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/summer camp': {
            #     'name': 'achievements/summer camp',
            #     'sync': 'Template:Dictionary/achievements/summer camp/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/foundry': {
            #     'name': 'achievements/foundry',
            #     'sync': 'Template:Dictionary/achievements/foundry/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/christmas': {
            #     'name': 'achievements/christmas',
            #     'sync': 'Template:Dictionary/achievements/christmas/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/astro-chievements': {
            #     'name': 'achievements/astro-chievements',
            #     'sync': 'Template:Dictionary/achievements/astro-chievements/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/mann vs. machievements': {
            #     'name': 'achievements/mann vs. machievements',
            #     'sync': 'Template:Dictionary/achievements/mann vs. machievements/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/standin': {
            #     'name': 'achievements/standin',
            #     'sync': 'Template:Dictionary/achievements/standin/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/process': {
            #     'name': 'achievements/process',
            #     'sync': 'Template:Dictionary/achievements/process/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/snakewater': {
            #     'name': 'achievements/snakewater',
            #     'sync': 'Template:Dictionary/achievements/snakewater/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/powerhouse': {
            #     'name': 'achievements/powerhouse',
            #     'sync': 'Template:Dictionary/achievements/powerhouse/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/other games': {
            #     'name': 'achievements/other games',
            #     'sync': 'Template:Dictionary/achievements/other games/Special:SyncData'
            # },
            # u'Template:Dictionary/achievements/pass time': {
            #     'name': 'achievements/pass time',
            #     'sync': 'Template:Dictionary/achievements/pass time/Special:SyncData'
            # },
            # u'Template:Dictionary/blueprints': {
            #     'name': 'blueprints',
            #     'sync': 'Template:Dictionary/blueprints/Special:SyncData'
            # },
            # u'Template:Dictionary/defindex': {
            #     'name': 'defindex',
            #     'sync': 'Template:Dictionary/defindex/Special:SyncData'
            # },
            # u'Template:Dictionary/quad': {
            #     'name': 'quad',
            #     'sync': 'Template:Dictionary/quad/Special:SyncData',
            #     'blankString': '-'
            # },
            # u'Template:Dictionary/gameinfo': {
            #     'name': 'gameinfo',
            #     'sync': 'Template:Dictionary/gameinfo/Special:SyncData'
            # }
        }
        self.subpageSeparator = u'/'
        # List of supported languages, in prefered order
        self.languages = [u'en', u'ar', u'bg', u'cs', u'da', u'de', u'es', u'fi', u'fr', u'hu', u'it', u'ja', u'ko', u'nl', u'no', u'pl', u'pt', u'pt-br', u'ro', u'ru', u'sv', u'th', u'tr', u'uk', u'vi', u'zh-hans', u'zh-hant']
        self.defaultLang = u'en'
        self.allKeyName = u'_all_'
        self.filterName = u'Your friendly neighborhood dictionary updater'
        self.commentsExtract = compileRegex(r'<!--([\S\s]+?)-->')
        self.subkeyName = compileRegex(r'^([-\w]+)$', re.IGNORECASE)
        addWhitelistPage(self.dictionaries.keys())
        self.editCounts = {}
    def updateSyncData(self, currentDict, syncData, note=''):
        # Build syncdata string representation
        syncKeys = list(syncData.keys())
        syncKeys.sort()
        syncLines = []
        for k in syncKeys:
            syncLines.append(k + u':' + syncData[k])
        if note:
            note = u' (' + u(note) + u')'
        editPage(self.dictionaries[currentDict]['sync'], u'\n'.join(syncLines), summary=u'Updated synchronization information for [[:' + currentDict + u']]' + note + u'.', minor=True, nocreate=False)
    def generateSubpage(self, keyName, data, currentDict, syncData):
        h = hashlib.md5()
        if type(data) is type({}): # Subkeys (translations or not)
            isTranslation = True
            subpage = u(self.subpageTemplateLang)
            for k in data:
                if 'blankString' in self.dictionaries[currentDict] and data[k] == self.dictionaries[currentDict]['blankString']:
                    data[k] = u''
                if isTranslation and k not in self.languages:
                    isTranslation = False
                    subpage = u(self.subpageTemplateParam)
            ordered = []
            unordered = {}
            if isTranslation:
                missing = []
                for lang in self.languages:
                    if lang in data:
                        ordered.append(lang + u'=' + data[lang])
                        unordered[lang] = data[lang]
                        h.update((lang + u'=' + data[lang]).encode('utf8'))
                    else:
                        missing.append(lang)
                        h.update((u'null-' + lang).encode('utf8'))
                if self.defaultLang in data:
                    ordered.insert(0, u'#default=' + data[self.defaultLang])
                if len(missing):
                    subpage = subpage.replace(u'%missing%', u"Languages missing: " + u', '.join(missing))
                else:
                    subpage = subpage.replace(u'%missing%', u"Supported languages: all")
            else: # Not a translation
                h.update('Any-')
                subkeys = data.keys()
                subkeys.sort()
                for k in subkeys:
                    ordered.append(k + u'=' + data[k])
                    unordered[k] = data[k]
                    h.update((k + u'=' + data[k]).encode('utf8'))
            if 'allTemplate' in self.dictionaries[currentDict] and (len(unordered) or len(self.dictionaries[currentDict]['allTemplate']['params'])):
                allKey = []
                keys = unordered.keys()
                keys.sort()
                for k in keys:
                    allKey.append(k + u'=' + unordered[k])
                insertIndex = 0
                if isTranslation and self.defaultLang in data:
                    insertIndex = 1
                ordered.insert(insertIndex, u(self.allKeyName) + u'=' + u(self.dictionaries[currentDict]['allTemplate'].replace(u'%options%', u'|'.join(allKey))))
            subpage = subpage.replace(u'%options%', u'|'.join(ordered))
        else: # No subkeys
            data = u(data)
            subpage = self.subpageTemplateID
            h.update(u(u'ID-' + data).encode('utf8'))
            subpage = subpage.replace(u'%string%', data)
        h = u(h.hexdigest())
        if keyName in syncData and syncData[keyName] == h:
            return # Same hash
        subpage = subpage.replace(u'%dictionary%', currentDict)
        subpage = subpage.replace(u'%dictionaryname%', self.dictionaries[currentDict]['name'])
        subpage = subpage.replace(u'%keyname%', keyName)
        pagename = self.dictionaries[currentDict].get('overridePath', currentDict) + self.subpageSeparator + keyName
        if editPage(pagename, subpage, summary=u'Pushed changes from [[:' + currentDict + u']] for string "' + keyName + u'".', minor=True, nocreate=False):
            syncData[keyName] = h # Update sync data
            if currentDict not in self.editCounts:
                self.editCounts[currentDict] = 0
            self.editCounts[currentDict] += 1
            if self.editCounts[currentDict] > self.partialUpdateThreshold:
                self.editCounts[currentDict] = 0
                self.updateSyncData(currentDict, syncData, 'Partial update')
    def dedup(self, l):
        s = set()
        for i in l:
            if i not in s:
                s.add(i)
                yield i
    def processComment(self, commentString, currentDict, definedStrings, syncData):
        commentContents = []
        commentString = u(commentString).replace(u'\r', u'')
        parseState = {
            'currentKeys': [],
            'currentSubkeys': {},
            'currentKeyIsValid': False,
            'abortCurrentSubkeys': False,
            'subKeyLines': {},
        }
        subPageData = {}
        def finalize():
            if parseState['currentKeyIsValid']:
                # End processing of current set of subkeys.
                if not parseState['abortCurrentSubkeys']:
                    isTranslation = True
                    for k in parseState['currentKeys']:
                        assert k not in subPageData, 'Internal logic consistency error: duplicate key %r' % (k,)
                        subPageData[k] = {}
                        for subKey, data in parseState['currentSubkeys'].items():
                            isTranslation = isTranslation and subKey in self.languages
                            subPageData[k][subKey] = data
                    if isTranslation:
                        for lang in self.languages:
                            if lang in parseState['subKeyLines']:
                                commentContents.append(parseState['subKeyLines'][lang])
                    else:
                        for subKey in sorted(parseState['subKeyLines'].keys()):
                            commentContents.append(parseState['subKeyLines'][subKey])
                    parseState['abortCurrentSubkeys'] = False
                parseState['currentKeyIsValid'] = False
        for line in commentString.split(u'\n'):
            if u'WINDBOT_INVALID' in line:
                commentContents.append(line)
                continue
            def badLine(reason):
                if parseState['abortCurrentSubkeys']:
                    for k in sorted(parseState['subKeyLines'].keys()):
                        commentContents.append(parseState['subKeyLines'][k] + u'  // WINDBOT_INVALID Other subkeys for this key are invalid')
                    parseState['subKeyLines'] = {}
                if parseState['currentKeyIsValid'] and not parseState['abortCurrentSubkeys']:
                    parseState['abortCurrentSubkeys'] = True
                else:
                    parseState['currentKeyIsValid'] = False
                commentContents.append(line + u'  // WINDBOT_INVALID ' + u(reason.replace(u':', ' ')))
            if line.strip() == u'':
                finalize()
                commentContents.append(line)
                continue
            if line.strip()[0] == u'#':  # Human comment
                commentContents.append(line)
                continue
            if line[0] not in (u' ', '\t'):  # Key, or key + no-subkey data
                if line.find(u':') == -1:  # Colon was probably forgotten
                    badLine('Maybe a forgotten colon?')
                    continue
                if parseState['currentKeyIsValid']:
                    badLine('Missing linebreak before new key?')
                    continue
                beforeColon, afterColon = line.split(u':', 1)
                afterColon = afterColon.strip()
                # Check keys.
                keyNames = [k.replace(u'_', u' ').replace(u'#', u'').strip().lower() for k in beforeColon.strip().split(u'|')]
                keyNames = [k for k in self.dedup(keyNames) if k]
                if len(keyNames) == 0:
                    badLine('No valid key names')
                    continue
                duplicateKey = None
                badKey = None
                for k in keyNames:
                    for c in self.invalidKeyNameCharacters:
                        if c in k:
                            badKey = k
                            break
                    if k in definedStrings:
                        duplicateKey = k
                        break
                    if k in subPageData:
                        duplicateKey = k
                        break
                if duplicateKey:
                    badLine('Duplicate key: %r' % duplicateKey)
                    continue
                if badKey:
                    badLine('Key has invalid characters: %r' % badKey)
                    continue
                # Key looks good.
                for k in keyNames:
                    definedStrings.add(k)
                # Check for no-subkey data.
                if afterColon:
                    for k in keyNames:
                        subPageData[k] = afterColon
                    commentContents.append(u' | '.join(keyNames) + u': ' + afterColon)
                else:
                    parseState['currentKeyIsValid'] = True
                    parseState['abortCurrentSubkeys'] = False
                    parseState['currentKeys'] = keyNames
                    parseState['currentSubkeys'] = {}
                    parseState['subKeyLines'] = {}
                    commentContents.append(u' | '.join(keyNames) + u':')
                continue
            # Sub-key definition follows (has a space as first character).
            if parseState['abortCurrentSubkeys']:
                commentContents.append(line)
                continue
            if not parseState['currentKeyIsValid']:
                badLine('Sub-key being defined despite no valid key')
                continue
            if line.find(u':') == -1:  # Colon was probably forgotten
                badLine('Missing colon in subkey definition')
                continue
            beforeColon, afterColon = line.strip().split(u':', 1)
            subKeyNames = [k.strip().lower() for k in beforeColon.strip().split(u'|')]
            subKeyNames = [k for k in self.dedup(subKeyNames) if k]
            badSubkeyName = None
            duplicateSubkey = None
            for k in subKeyNames:
                if not self.subkeyName.match(k):
                    badSubkeyName = k
                    break
                if k in parseState['currentSubkeys'].keys():
                    duplicateSubkey = k
                    break
            if badSubkeyName:
                badLine('Invalid subkey name: %r' % badSubkeyName)
                continue
            if duplicateSubkey:
                badLine('Duplicate subkey name: %r' % duplicateSubkey)
                continue
            subKeyData = afterColon.strip()
            if not subKeyData:
                badLine('Empty data')
                continue
            for k in subKeyNames:
                parseState['currentSubkeys'][k] = subKeyData
                parseState['subKeyLines'][k] = u'  ' + k + u': ' + subKeyData
        finalize()
        for k, data in subPageData.items():
            self.generateSubpage(k, data, currentDict, syncData)
        return u'\n'.join(commentContents)
    def __call__(self, content, **kwargs):
        if 'article' not in kwargs:
            return content
        if u(kwargs['article'].title) not in self.dictionaries:
            return content
        currentDict = u(kwargs['article'].title)
        if random.randint(0, 50) == 0: # With probability 2%, ignore syncdata completely. Helps with stale syncdata and people overwriting things.
            syncDataText = u''
        else:
            try:
                syncDataText = u(page(self.dictionaries[currentDict]['sync']).getWikiText()).split(u'\n')
            except: # Page probably doesn't exist
                syncDataText = u''
        syncData = {}
        for sync in syncDataText:
            sync = u(sync.strip())
            if not sync:
                continue
            sync = sync.split(u':', 1)
            if len(sync) == 2:
                syncData[sync[0]] = sync[1]
        oldSyncData = syncData.copy()
        newContent = u''
        previousIndex = 0
        definedStrings = set()
        for comment in self.commentsExtract.finditer(content):
            newContent += content[previousIndex:comment.start()]
            previousIndex = comment.end()
            # Process current comment
            newContent += u'<!--\n\n' + self.processComment(u(comment.group(1)).strip(), currentDict, definedStrings, syncData) + u'\n\n-->'
        newContent += content[previousIndex:]
        # Check for deleted strings
        for k in oldSyncData:
            if k not in definedStrings:
                try:
                    deletePage(currentDict + self.subpageSeparator + k, 'Removed deleted string "' + k + u'" from [[:' + currentDict + u']].')
                except:
                    pass
                if k in syncData:
                    del syncData[k]
        self.updateSyncData(currentDict, syncData, 'Full update')
        self.editCounts[currentDict] = 0
        return newContent


from wikitools.wiki import Wiki
from wikitools.page import Page

w = Wiki('https://wiki.teamfortress.com/w/api.php')

updater = DictionaryUpdater()
for title in updater.dictionaries:
  page = Page(w, title)
  print(f'Updating {page}')

  # old_content = page.get_wiki_text()
  old_content = ''' \
{{Dictionary/header}}
<div style="margin-top: 1em;">
:{{c|info|Important!}} It is strongly recommended ''not'' to edit this whole page at once, as the page size is very large. Use the [edit] section links and make multiple edits instead.
</div>

== Weapons ==
=== Scout weapons ===

==== Scout Primary ====
<!--

# TF_Weapon_PEP_Scattergun
baby face's blaster:
  en: Baby Face's Blaster
  da: Dengsedrengens Dræber
  de: Babyfaces Ballermann
  es: Devastadora del Imberbe
  fi: Pikkupojan paukkurauta
  fr: Exploseur de Tête d'Ange
  hu: Babaarc Beütője
  it: Fucile di Baby Face
  ko: 동안의 총
  nl: Kinderbakkesknaller
  no: Barneansiktets bankraner
  pl: Browning Baby Face'a
  pt: Bacamarte do 'Baby Face'
  pt-br: Destruidora do Degenerado
  ru: Обрез Малыша
  sv: Barnansiktets Blästrare
  tr: Bebek Yüzlünün Ateşleyicisi
  zh-hans: 娃娃脸的冲击波
  zh-hant: 型男霰彈槍

-->'''
  
  new_content = updater(old_content, article=page)

  print(len(new_content))

  raise