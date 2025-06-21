# A very light smattering of tests
import inspect
import sys
from wikitools.wiki import Wiki
from wikitools.page import Page
from reports.untranslated_templates import parse_lang_templates, parse_lang_templates2

class MockWiki(Wiki):
  def get_namespaces(self):
    return {}


raw_text = """{{Ambox
| type    = content
| image   = Five Second Plan Icon.png
| contents= {{ambox/message
 | 1 = {{lang
  | en = What are you lookin' at?!
  | es = ¿¡Tú qué miras!?
  | fr = Qu'est-ce que tu regardes ?
  | pl = Na co się gapisz?!
  | pt-br = O que é que cê ta olhando?!
  | ro = La ce te uiți?! 
  | ru = Куда вы смотрите?
  | sv = Vad kollar du på?
  | zh-hans = 你在看什么呢？
  }}
 | 2 = {{lang
  | en = This page or section would benefit from the addition or updating of one or more 3D views.
  | es = Esta página o sección ganaría mucho si alguien añadiese o actualizase una o más vistas 3D.
  | fr = Cette page ou section pourrait bénéficier de l’ajout ou de la mise à jour d’une ou plusieurs vues en 3D.
  | pl = Ta strona lub sekcja zyskałaby na dodaniu lub aktualizacji jednego lub więcej widoków 3D.
  | pt-br = Esta página ou seção se beneficiaria da adição ou atualização de uma ou mais visualizações em 3D.
  | ro = Această pagină sau secțiune ar putea beneficia de adăugarea sau actualizarea unui model 3D.
  | ru = У этой статьи или раздела нет 3D-иллюстраций или они нуждаются в обновлении.
  | sv = Denna sida eller sektion skulle kunna behöva ha flera eller uppdatera en eller flera av dess 3D bilder.
  | zh-hans = 新增几张相关的3D图片能为这个页面或部分增色。
  }}
 | 3 = {{lang
  | en = Please add a suitable 3D image or update the existing ones, then remove this notice.
  | es = Por favor, si tienes la posibilidad, añade una imagen 3D o actualiza las existentes, si lo haces, elimina este aviso. 
  | fr = Veuillez ajouter une image 3D appropriée ou mettre à jour les existantes, puis retirez ce bandeau.
  | pl = Dodaj odpowiedni obraz 3D lub zaktualizuj istniejący, a następnie usuń to powiadomienie.
  | pt-br = Por favor, adicione uma imagem em 3D adequada ou atualize as existentes e remova este aviso.
  | ro = Vă rugăm adăugați o imagine 3D adecvată sau actualizați una deja existentă, apoi ștergeți această observație.
  | ru = Пожалуйста, добавьте или обновите изображения, а затем уберите это предупреждение.
  | sv = Var snäll och lägg till en lämplig 3D bild eller uppdatera de som redan finns, och sedan ta bort denna notis. 
  | zh-hans = 请帮助补上几张适宜的3D图片或更新已有的，再移除该提示。
  }}{{#if:{{{1|{{{note|}}}}}}
   | &nbsp;{{lang
    | en = The specific instructions are:
    | es = Las instrucciones específicas son:
    | fr = Les instructions spécifiques sont :
    | pl = Szczegółowe instrukcje:
    | pt-br = As instruções específicas são:
    | ro = Instrucțiunile specifice sunt:
    | ru = Примечание:
    | sv = Den specifika instruktionen är:
    | zh-hans = 具体说明： 
    }}&nbsp;"''{{{1|{{{note|}}}}}}''"
   }}
 }}
}}<includeonly>[[Category:Articles needing 3D views|{{BASEPAGENAME}}]]</includeonly><noinclude>
{{translation switching|en, es, fr, pl, pt-br, ro, ru, sv, zh-hans}}
{{Doc begin}}
== Usage ==
* Place {{tl|Need3d}} on a page that needs 3D views added or updated.
* You may also use the first parameter to add instructions or detail to the requst &ndash; e.g. {{tlx|Need3d|instructions }}
* This will place the page in [[:Category:Articles needing 3D views]].


[[Category:Maintenance templates|Needimage]]
[[Category:Image insertion templates|Needimage]]
[[Category:Templates|Needimage]]
</noinclude>"""

class Tests:
  # Class setup

  #############
  #!# Tests #!#
  #############

  def test_lang_parser(self):
    w = MockWiki('https://wiki.teamfortress.com/w/api.php')
    p = Page(w, 'Template:Enforcer bypassed resistances')
    for text in [raw_text]:
      # w.page_text_cache[p.title] = text
      l1 = parse_lang_templates(p)
      l2 = parse_lang_templates2(p)
      assert len(l1) == len(l2), f'{len(l1)} != {len(l2)}\n{l1}\n{l2}'
      for i in range(len(l1)):
        assert l1[i]['template'] == l2[i]['template'], f'{l1[i]["template"]} != {l2[i]["template"]}'
        assert l1[i]['location'] == l2[i]['location'], f'{l1[i]["location"]}\n!=\n{l2[i]["location"]}'
        assert l1[i]['args'] == l2[i]['args']


if __name__ == '__main__':
  tests = Tests()

  def is_test(method):
    return inspect.ismethod(method) and method.__name__.startswith('test')
  tests = list(inspect.getmembers(tests, is_test))
  tests.sort(key=lambda func: func[1].__code__.co_firstlineno)

  for test in tests:
    if len(sys.argv) > 1: # Requested specific test(s)
      if test[0] not in sys.argv[1:]:
        continue

    # Test setup (nothing yet)

    # Run test
    print('---', test[0], 'started')
    try:
      test[1]()
    except Exception:
      print('!!!', test[0], 'failed:')
      import traceback
      traceback.print_exc()
      sys.exit(-1)

    print('===', test[0], 'passed')
  print('\nAll tests passed')
