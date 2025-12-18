'''
For further detail/future revisions, visit 
https://shyam.saladi.org/pymol_viridis

DESCRIPTION
    Makes perceptually uniform and colorblind accessible color palettes
    available in PyMOL

    Certain colors are indistinguishable to people with the various forms of
    color blindness, and therefore are better not used in figures intended for
    public viewing. This script provides additional color palettes to allow for
    an alternative to the default rainbow coloring that is unambiguous both to
    colorblind and non-colorblind people.

    By running this script,
        * default color palette for `spectrum` is changed to turbo
        * viridis options are added to menus.

    Color scale details:
        - viridis, magma, inferno, plasma: Stéfan van der Walt, Nathaniel Smith,
            & Eric Firing. https://bids.github.io/colormap
        - cividis: Jamie Nuñez, Christopher Anderton, Ryan Renslow.
                    https://doi.org/10.1371/journal.pone.0199239
        - turbo: Anton Mikhailov.
                https://ai.googleblog.com/2019/08/turbo-improved-rainbow-colormap-for.html
    
    Pymol script colorblindfriendly.py by @jaredsampson used as reference for modifying menus:
        https://github.com/Pymol-Scripts/Pymol-script-repo/blob/master/colorblindfriendly.py

USAGE

    Simply run this script. 
    To unpatch `spectrum` and remove viridis menus from graphical interface,
    run `remove_viridis_menus()`.

REQUIREMENTS

    The new menus (`add_viridis_menus()` and `remove_viridis_menus()`)
    require PyMOL 1.6.0 or later.

AUTHOR

    Shyam Saladi
    Github: @smsaladi

LICENSE (MIT)

Copyright (c) 2019 Shyam Saladi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


Palette RGB values is taken from bokeh.palettes.
Corresponding copyrights notices can be found here:
https://github.com/bokeh/bokeh/blob/b19f2c5/bokeh/palettes.py

'''
import functools

from typing import List, Tuple, Dict, Any, Optional
from pymol import cmd, viewing, menu # type: ignore
from palettes_data import NEW_PALETTES

__author__ = 'Shyam Saladi'
__version__ = '0.0.1'


# Global variables to store original functions
_original_spectrum: Optional[Any] = None
_original_by_chain: Optional[Any] = None
_original_mol_color: Optional[Any] = None
_original_color_auto: Optional[Any] = None

'''Add/configure palettes used by `spectrum`
'''
def patch_spectrum() -> None:
    '''Monkey-patches spectrum to set the default palette to `turbo`
    '''
    global _original_spectrum
    if _original_spectrum is None:
        _original_spectrum = cmd.spectrum

    @functools.wraps(_original_spectrum)
    def spectrum_wrapper(*args: Any, **kwargs: Any) -> Any:
        # If palette (2nd arg) is not provided, set default to 'turbo'
        if len(args) < 2 and 'palette' not in kwargs:
            kwargs['palette'] = 'turbo'
        return _original_spectrum(*args, **kwargs)

    cmd.spectrum = spectrum_wrapper
    return

def unpatch_spectrum() -> None:
    '''Resets default color palette to `rainbow`
    '''
    global _original_spectrum
    if _original_spectrum is not None:
        cmd.spectrum = _original_spectrum
        _original_spectrum = None
    return

def viridis(*args: Any, **kwargs: Any) -> None:
    '''New command to color using viridis
    '''
    if len(args) >= 1:
        args_list = list(args)
        args_list[1] = 'viridis'
        args = tuple(args_list)
    else:
        kwargs['palette'] = 'viridis'
    cmd.spectrum(*args, **kwargs)
cmd.extend(viridis)


def add_palettes() -> None:
    '''Add the color blind-friendly colormaps/palettes to PyMOL.'''
    def format_colors(values: List[str]) -> str:
        return ' '.join(values).replace('#', '0x')

    for pal_name, values in NEW_PALETTES.items():
        viewing.palette_colors_dict[pal_name] = format_colors(values)

    # Notify user of newly available colors
    print('`' + '`, `'.join(NEW_PALETTES.keys()) + '`')
    return


'''Add Viridis options to menus

Under `C` menu:
    Adds to menus: `by_chain` & `auto`
        - Does this by monkey-patching the current menus
    Creates a new menu: `viridis` (like `spectrum`)

Some parts adapted from
https://github.com/schrodinger/pymol-open-source/blob/6ca016e82a5cf9febc064ee5a15ab505d51ec8c7/modules/pymol/menu.py

'''

def _viridis_menu(self_cmd: Any, sele: str) -> List[Any]:
    viridis_col = _colorize_text('viridis')

    r = [
        [2, 'Viridis:', ''],
        [1, viridis_col + '(elem C)',
            'cmd.spectrum("count", "viridis", selection="('+sele+') & elem C")'   ],
        [1, viridis_col + '(*/CA)'  ,
            'cmd.spectrum("count", "viridis", selection="('+sele+') & */CA")'     ],
        [1, viridis_col             ,
            'cmd.spectrum("count", "viridis", selection="'+sele+'", byres=1)'     ],
        [0, '', ''],
        [1, 'b-factors'             ,
            'cmd.spectrum("b", "viridis", selection=("'+sele+'"), quiet=0)'       ],
        [1, 'b-factors(*/CA)'       ,
            'cmd.spectrum("b", "viridis", selection="(('+sele+') & */CA)", quiet=0)'],
        [0, '', ''],
        [1, 'area (molecular)'      ,
            'util.color_by_area(("'+sele+'"), "molecular", palette="viridis")'    ],
        [1, 'area (solvent)'        ,
            'util.color_by_area(("'+sele+'"), "solvent", palette="viridis")'      ],
        ]
    with menu.menucontext(self_cmd, sele) as mc:
        r += [
            [0, '', ''],
            [1, 'user properties', [[ 2, 'User Properties:', '' ]] + [
                [ 1, key, [[ 2, 'Palette', '' ]] + [
                    [1, palette, 'cmd.spectrum("properties[%s]", "%s", "%s")' % (repr(key), palette, sele)]
                    for palette in ('viridis', 'blue white red', 'green red')
                ]] for key in mc.props
            ]],
        ]
    return r


def _by_chain_patch(self_cmd: Any, sele: str) -> List[Any]:
    by_chain_col = _colorize_text('by chain')
    by_segi_col = _colorize_text('by segi ')
    chainbows_col = _colorize_text('chainbows')
    
    if _original_by_chain is None:
        return []

    r = _original_by_chain(self_cmd, sele) + [
        [0, '', ''],
        [0, '', ''],
        [1, by_chain_col + '(elem C)',
            'util.color_chains("('+sele+' and elem C)", palette="viridis", _self=cmd)'],
        [1, by_chain_col + '(*/CA)',
            'util.color_chains("('+sele+' and name CA)", palette="viridis", _self=cmd)'],
        [1, by_chain_col,
            'util.color_chains("('+sele+')", palette="viridis", _self=cmd)'],
        [0, '', ''],
        [1, chainbows_col,
            'util.chainbow("('+sele+')", palette="viridis", _self=cmd)'],
        [0, '', ''],
        [1, by_segi_col + '(elem C)',
            'cmd.spectrum("segi", "viridis", "('+sele+') & elem C")'],
        [1, by_segi_col,
            'cmd.spectrum("segi", "viridis", "' + sele + '")'],
        ]
    return r

def _color_auto_patch(self_cmd: Any, sele: str) -> List[Any]:
    by_obj_col = _colorize_text('by obj')
    by_obj_c_col = _colorize_text('by obj(elem C)')
    chainbows_col = _colorize_text('chainbows')
    
    if _original_color_auto is None:
        return []

    r = _original_color_auto(self_cmd, sele) + [
        [ 0, '', ''],
        [ 1, by_obj_col,
          'util.color_objs("('+sele+' and elem C)", palette="viridis", _self=cmd)'],
        [ 1, by_obj_c_col,
          'util.color_objs("('+sele+')", palette="viridis", _self=cmd)'],
        ]
    return r

def _mol_color_patch(self_cmd: Any, sele: str) -> List[Any]:
    viridis_col = _colorize_text('viridis')
    
    if _original_mol_color is None:
        return []

    with menu.menucontext(self_cmd, sele):
        for i, item in enumerate(_original_mol_color(self_cmd, sele)):
            _, text, _ = item
            if text == 'auto':
                auto_menu_idx = i
                break
        
        r = _original_mol_color(self_cmd, sele)
        r.insert(auto_menu_idx - 1, [1, viridis_col, _viridis_menu(self_cmd, sele)])
        return r

def _has_viridis_palettes() -> bool:
    for k in NEW_PALETTES.keys():
        if k not in viewing.palette_colors_dict.keys():
            return False
    return True

def add_viridis_menus() -> None:
    '''Add viridis options to the PyMOL OpenGL menus where spectrum options exist
    '''

    if hasattr(menu, 'has_viridis_menus') and menu.has_viridis_menus:
        print('Palette menus were already added!')
        return

    # Make sure palettes are installed.
    if not _has_viridis_palettes():
        print('Adding palettes...')
        add_palettes()

    print('Changing default palette for spectrum to `turbo`')
    patch_spectrum()

    # Abort if PyMOL is too old.
    try:
        from pymol.menu import all_colors_list
    except ImportError:
        print('PyMOL version too old for palettes menus. Requires 1.6.0 or later.')
        return
    
    # These will each be monkey-patched
    global _original_by_chain, _original_mol_color, _original_color_auto
    
    if _original_by_chain is None:
        _original_by_chain = menu.by_chain
    if _original_mol_color is None:
        _original_mol_color = menu.mol_color
    if _original_color_auto is None:
        _original_color_auto = menu.color_auto

    # Add the menu
    print('Adding viridis to menus...')
    menu.by_chain = _by_chain_patch
    menu.mol_color = _mol_color_patch
    menu.color_auto = _color_auto_patch

    menu.has_viridis_menus = True
    print('Done!')

    return

def remove_viridis_menus() -> None:
    '''Removes viridis options to the PyMOL OpenGL menus
    '''

    print('Changing default palette for spectrum back to `rainbow`')
    unpatch_spectrum()

    if not hasattr(menu, 'has_viridis_menus') or not menu.has_viridis_menus:
        print('Palette menus are not present!')
        return

    # Abort if PyMOL is too old.
    try:
        from pymol.menu import all_colors_list
    except ImportError:
        print('PyMOL version too old for palettes menus. Requires 1.6.0 or later.')
        return

    print('Removing viridis from menus...')
    global _original_by_chain, _original_mol_color, _original_color_auto
    
    if _original_by_chain is not None:
        menu.by_chain = _original_by_chain
        _original_by_chain = None
    
    if _original_mol_color is not None:
        menu.mol_color = _original_mol_color
        _original_mol_color = None

    if _original_color_auto is not None:
        menu.color_auto = _original_color_auto
        _original_color_auto = None

    menu.has_viridis_menus = False
    print('Done!')

    return


'''Help with generating colorized text for menus

\\RGB represents colors in 'decimal' format, i.e. 0-9 for R, 0-9 for G, 0-9 for B.
This function converts 16-bit hex colors `#RRGGBB` into this format. It was initially
used, but for efficency the \\RGB values are hard coded below
'''
def _convert_hex_color(color: str) -> str:
    chex = color[1:]
    rgb = cmd.get_color_tuple('0x' + chex)
    rgb_list = [str(int(v * 9)) for v in rgb]
    return ''.join(rgb_list)

# last 8 for viridis10 (first two are too dark -- hard to see text on black background)
# _viridis8 = ['#3E4989', '#30678D', '#25828E', '#1E9C89', '#35B778', '#6BCD59', '#B2DD2C', '#FDE724']
# viridis8_rgb = [_convert_hex_color(c) for c in _viridis8]
_viridis8_rgb = ['224', '134', '145', '154', '164', '373', '671', '881']

def _colorize_text(text: str, palette: Tuple[str, ...] = tuple(_viridis8_rgb)) -> str:
    '''Colorizes text given a list of RGB color values (NNN format)
    '''
    text_list = list(text)
    palette_list = list(palette)
    
    palette_list.append('888') # last character white again
    palette_list = palette_list[:min(len(palette_list), len(text_list))]
    for i, col in enumerate(palette_list):
        if text_list[i] == '(':
            text_list[i] = '\\%s%s' % ('888', text_list[i])
            break
        text_list[i] = '\\%s%s' % (col, text_list[i])

    return ''.join(text_list) + '\\888'



if __name__ == 'pymol':
    add_viridis_menus()
