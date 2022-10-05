[![TFWiki Stats](https://github.com/jbzdarkid/TFWiki-scripts/actions/workflows/tfwiki_stats.yml/badge.svg)](https://github.com/jbzdarkid/TFWiki-scripts/actions/workflows/tfwiki_stats.yml)

A collection of scripts used to generate reports for the [TF2 Wiki](https://wiki.teamfortress.com/wiki/Team_Fortress_Wiki:Reports)

This version of the scripts has been updated to python3, which unfortunately broke wikitools.  A stripped-down, python3-compatible version is checked in to this repo.

## Daily reports
- `all_articles.py`: Generates the complete list of translated articles for each language, which is used by the translator's noticeboard
- `missing_translations.py`: Generates the list of missing translations for each language compared to english, which is used by the translator's noticeboard
- `untranslated_templates.py`: Parses templates for {{lang}} usage, and reports whether or not they are fully translated.

## Weekly reports
- `incorrectly_categorized.py`: Searches all categories for articles which are categorized into the wrong language
- `incorrectly_categorized.py`: Searches all language pages for links to other languages (e.g. /es linking to /pt).
- `navboxes.py`: Looks for navboxes (display-only templates which crosslink many articles) that are not present on all of their article pages.
- `wanted_templates.py`: Searches for template transclusions which don't exist, usually indicative of a typo.
modules_to_run += [ 'navboxes', 'overtranslated', 'missing_categories']

## Monthly reports
- `displaytitles.py`: Searches for pages with duplicate displaytitles, which show a gross-looking error message.
- `duplicate_files.py`: Finds all identical files, and sorts them by usage count.
- `edit_stats.py`: Provides some statistics about user editing habits on the wiki, along with a list of the top 100 editors by edit count
- `external_links2.py`: Searches all articles for links outside the tf2 wiki, and checks to see if those links are still valid (HTTP 200)
- `mismatched.py`: Searches all articles for incorrect pairs of parenthesis, to help catch broken links, tags, and templates.
- `missing_categories.py`: Searches for non-translated categories. Categories which are only in english should generally be marked as {{non-article category}}.
- `overtranslated.py`: Searches all articles for language pages which don't exist in english. This is usually indicative of duplicate translations.
- `undocumented_templates.py`: Parses all templates to see if they have sufficient text in <noinclude> or {{documentation}}
- `unused_files.py`: Reparses Special:UnusedFiles, and re-sorts the data, along with removing some known exceptions.
