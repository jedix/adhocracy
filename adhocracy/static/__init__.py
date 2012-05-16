from fanstatic import Library, Group, Resource, init_needed
# external libraries
from js.jquery import jquery
from js.jquery_joyride import joyride
from js.socialshareprivacy import socialshareprivacy


# --[ yaml ]----------------------------------------------------------------

yaml_library = Library('yaml', 'yaml')
yaml_base = Resource(yaml_library, 'core/base.css')
yaml_print = Resource(yaml_library, 'print/print_draft.css',
                      depends=[yaml_base])
yaml = Group([yaml_base, yaml_print])

# --[ twitter bootstrap ]---------------------------------------------------

bootstrap_library = Library('bootstrap', 'bootstrap', version="2.0.3")
bootstrap_js = Resource(bootstrap_library, 'js/bootstrap.js',
                        minified='js/bootstrap.min.js',
                        depends=[jquery])
bootstrap_css = Resource(bootstrap_library, 'css/bootstrap.css',
                         minified='css/bootstrap.min.css',
                         depends=[yaml])  # include it after yaml
bootstrap = Group([bootstrap_js, bootstrap_css])


# --[ stylesheets ]---------------------------------------------------------

stylesheets_library = Library('stylesheets', 'stylesheets')
fonts = Resource(stylesheets_library, 'screen/fonts.css',
                   depends=[yaml, bootstrap_css])
basemod = Resource(stylesheets_library, 'screen/basemod.css',
                   depends=[fonts])
content = Resource(stylesheets_library, 'screen/content.css',
                   depends=[basemod])
style = Resource(stylesheets_library, 'style.css',
                 depends=[content])
stylesheets = Group([yaml, fonts, basemod, content, style])


# --[ jquery.autocomplete ]-------------------------------------------------

autocomplete_library = Library('autocomplete', 'javascripts')
autocomplete_js = Resource(autocomplete_library, 'jquery.autocomplete.min.js',
                           depends=[jquery])
autocomplete_css = Resource(autocomplete_library, 'jquery.autocomplete.css')
autocomplete = Group([autocomplete_js, autocomplete_css])


# --[ jquerytools ]---------------------------------------------------------

jquerytools_library = Library('jquerytools', 'javascripts')
jquerytools = Resource(jquerytools_library, 'jquery.tools.min.js',
                       depends=[jquery])


# --[ misc javascripts ]----------------------------------------------------

misc_library = Library('misc', 'javascripts')
elastic = Resource(misc_library, 'jquery.elastic.js',
                   depends=[jquery])
label_over = Resource(misc_library, 'jquery.label_over.js',
                      depends=[jquery])
cycle = Resource(misc_library, 'jquery.multipleelements.cycle.min.js',
                 depends=[jquery])
modernizr = Resource(misc_library, 'modernizr.js',
                     depends=[jquery])


# --[ adhocracy ]-----------------------------------------------------------

adhocracy_library = Library('adhocracy', 'javascripts')
adhocracy = Resource(adhocracy_library, 'adhocracy.js',
                     depends=[jquery, bootstrap_js, elastic,
                              label_over, modernizr])


# --[ knockout ]------------------------------------------------------------

knockout_library = Library('knockoutjs', 'javascripts')
knockout_js = Resource(knockout_library, 'knockout-latest.js',
                       depends=[jquery])
knockout_mapping_js = Resource(knockout_library, 'knockout-mapping.js',
                               depends=[knockout_js])
knockout = Group([knockout_js, knockout_mapping_js])
adhocracy_ko = Resource(knockout_library, 'adhocracy.ko.js',
                        depends=[adhocracy, knockout])



