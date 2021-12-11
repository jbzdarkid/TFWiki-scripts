[![TFWiki Stats](https://github.com/jbzdarkid/TFWiki-scripts/actions/workflows/tfwiki_stats.yml/badge.svg)](https://github.com/jbzdarkid/TFWiki-scripts/actions/workflows/tfwiki_stats.yml)

A collection of scripts used to generate reports for the [TF2 Wiki](https://wiki.teamfortress.com/wiki/Team_Fortress_Wiki:Reports)

This version of the scripts has been updated to python3, which unfortunately broke wikitools.  A stripped-down, python3-compatible version is checked in to this repo.

## Daily reports
- `untranslated_templates.py`: Parses templates for {{lang}} usage, and reports whether or not they are fully translated.
- `missing_translations.py`: Generates the list of missing translations for each language compared to english, which is used by the translator's noticeboard
- `all_articles.py`: Generates the complete list of translated articles for each language, which is used by the translator's noticeboard

## Weekly reports
(none so far)

## Monthly reports
- `edit_stats.py`: Provides some statistics about user editing habits on the wiki, along with a list of the top 100 editors by edit count
- `undocumented_templates.py`: Parses all templates to see if they have sufficient text in <noinclude> or {{documentation}}
- `unused_files.py`: Reparses Special:UnusedFiles, and re-sorts the data, along with removing some known exceptions.
- `duplicate_files.py`: Finds all identical files, and sorts them by usage count.
- `external_links.py`: Searches all articles for links outside the tf2 wiki, and checks to see if those links are still valid (HTTP 200)
- `mismatched.py`: Searches all articles for incorrect pairs of parenthesis, to help catch broken links, tags, and templates.
