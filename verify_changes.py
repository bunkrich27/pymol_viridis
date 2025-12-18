import sys
from unittest.mock import MagicMock, patch
import types

# Mock pymol structure
pymol = types.ModuleType('pymol')
cmd = types.ModuleType('pymol.cmd')
viewing = types.ModuleType('pymol.viewing')
menu = types.ModuleType('pymol.menu')

pymol.cmd = cmd
pymol.viewing = viewing
pymol.menu = menu

# Setup mocks
cmd.spectrum = MagicMock()
# Set __defaults__ for the mock to simulate original function
cmd.spectrum.__defaults__ = (None, 'rainbow', 'all', None, None, 0)
cmd.extend = MagicMock()

viewing.palette_colors_dict = {}

# Mock menu functions
def original_by_chain(self_cmd, sele): return [['original_by_chain']]
def original_mol_color(self_cmd, sele): return [['original_mol_color', 'auto', '']]
def original_color_auto(self_cmd, sele): return [['original_color_auto']]

menu.by_chain = original_by_chain
menu.mol_color = original_mol_color
menu.color_auto = original_color_auto
menu.all_colors_list = [] # Required by script

# Inject into sys.modules
sys.modules['pymol'] = pymol
sys.modules['pymol.cmd'] = cmd
sys.modules['pymol.viewing'] = viewing
sys.modules['pymol.menu'] = menu

# Now import the script to test
import viridispalettes

def test_add_menus():
    print("Testing add_viridis_menus...")
    viridispalettes.add_viridis_menus()
    
    # Check if palettes added
    if 'viridis' not in viewing.palette_colors_dict:
        print("FAIL: 'viridis' not added to palette_colors_dict")
        return False
    
    # Check if spectrum is wrapped
    if cmd.spectrum == viridispalettes._original_spectrum:
        print("FAIL: cmd.spectrum was not wrapped")
        return False
        
    # Check if menu functions are replaced
    if menu.by_chain == original_by_chain:
        print("FAIL: menu.by_chain was not patched")
        return False
        
    print("PASS: add_viridis_menus")
    return True

def test_spectrum_wrapper():
    print("Testing spectrum wrapper...")
    # Reset mock
    viridispalettes._original_spectrum.reset_mock()
    
    # Call without palette
    cmd.spectrum("count", selection="all")
    
    # Check if called with 'turbo'
    call_args = viridispalettes._original_spectrum.call_args
    if not call_args:
        print("FAIL: original spectrum not called")
        return False
        
    args, kwargs = call_args
    if kwargs.get('palette') != 'turbo':
        print(f"FAIL: expected palette='turbo', got {kwargs.get('palette')}")
        return False
        
    print("PASS: spectrum wrapper defaults to turbo")
    return True

def test_remove_menus():
    print("Testing remove_viridis_menus...")
    viridispalettes.remove_viridis_menus()
    
    # Check if spectrum is restored
    # Check if spectrum is restored
    # The wrapper does not have __defaults__ set, but our mock does.
    if not hasattr(cmd.spectrum, '__defaults__') or cmd.spectrum.__defaults__ != (None, 'rainbow', 'all', None, None, 0):
        print("FAIL: cmd.spectrum was not restored to original")
        return False

    # Check if menu functions are restored
    if menu.by_chain != original_by_chain:
        print("FAIL: menu.by_chain not restored")
        return False
        
    print("PASS: remove_viridis_menus")
    return True

def test_cmd_extend():
    print("Testing cmd.extend...")
    # We expect cmd.extend to have been called with viridispalettes.viridis
    # Since we don't have easy access to the exact function object passed unless we import it, 
    # we can check if it was called at all.
    if not cmd.extend.called:
        print("FAIL: cmd.extend not called")
        return False
    
    # Optional: check args
    args, _ = cmd.extend.call_args
    if args[0].__name__ != 'viridis':
        print(f"FAIL: cmd.extend called with {args[0].__name__}, expected 'viridis'")
        return False

    print("PASS: cmd.extend called with viridis")
    return True

if __name__ == "__main__":
    if test_add_menus() and test_spectrum_wrapper() and test_cmd_extend() and test_remove_menus():
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
