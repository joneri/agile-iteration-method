"""Regression checks for focus and viewport restoration on background updates."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


SCRIPT = (Path(__file__).resolve().parents[1] / "aim-ui/app.js").read_text()
HELPERS = SCRIPT[SCRIPT.index("function restoreFocus("):SCRIPT.index("function setConnection(")]


@unittest.skipUnless(shutil.which("node"), "Node is required")
class ViewportTests(unittest.TestCase):
    def run_js(self, scenario):
        host = """
const positions = {left: 0, top: 3500};
const calls = [];
let panels = [{id: 'kanban-panel', scrollLeft: 900, scrollTop: 80},
              {id: 'story-board', scrollLeft: 500, scrollTop: 0}];
function element(id) {
  return {id, scrollLeft: 0, scrollTop: 0,
    scrollTo({left, top, behavior}) { this.scrollLeft = left; this.scrollTop = top; calls.push([id, behavior]); },
    focus(options) { if (!options?.preventScroll) positions.top = 197; document.activeElement = this; }};
}
let targets = Object.fromEntries(panels.map(p => [p.id, element(p.id)]));
targets.filter = element('filter');
const document = {body: {}, activeElement: null, querySelectorAll: () => panels};
document.activeElement = document.body;
const $ = id => targets[id];
const window = {get scrollX() {return positions.left;}, get scrollY() {return positions.top;},
 scrollTo({left, top, behavior}) { positions.left = left; positions.top = top; calls.push(['window', behavior]); }};
"""
        result = subprocess.run(["node", "-e", host + HELPERS + scenario],
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_restoring_focus_does_not_scroll_back_to_old_control(self):
        result = self.run_js("""
restoreFocus({kind:'id', value:'filter'});
console.log(JSON.stringify({top:positions.top, focused:document.activeElement.id}));
""")
        self.assertEqual(result, {"top": 3500, "focused": "filter"})

    def test_restores_page_and_replaced_panel_offsets_synchronously(self):
        result = self.run_js("""
const saved = captureViewport();
positions.top = 197;
restoreViewport(saved);
console.log(JSON.stringify({top:positions.top, panels:Object.values(targets).slice(0,2).map(p=>[p.scrollLeft,p.scrollTop]), calls}));
""")
        self.assertEqual(result["top"], 3500)
        self.assertEqual(result["panels"], [[900, 80], [500, 0]])
        self.assertEqual(result["calls"], [["kanban-panel", "instant"], ["story-board", "instant"], ["window", "instant"]])

    def test_removed_panel_is_safe_and_user_navigation_has_no_restore(self):
        result = self.run_js("""
restoreViewport(null);
const before = calls.length;
const saved = captureViewport();
delete targets['kanban-panel'];
restoreViewport(saved);
console.log(JSON.stringify({before, calls}));
""")
        self.assertEqual(result["before"], 0)
        self.assertEqual(result["calls"], [["story-board", "instant"], ["window", "instant"]])


if __name__ == "__main__":
    unittest.main()
