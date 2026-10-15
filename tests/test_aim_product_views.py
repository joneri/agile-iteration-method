"""Execute the product UI model, handoff boundaries and active-view dispatch."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_SCRIPT = (ROOT / "aim-ui/product-views.js").read_text(encoding="utf-8")
APP = (ROOT / "aim-ui/app.js").read_text(encoding="utf-8")
PURE = PRODUCT_SCRIPT[:PRODUCT_SCRIPT.index("function productOpenInCodex(")]
HASH = "a" * 64
SCOPE = "b" * 64


def source_function(start, end):
    return APP[APP.index("function " + start):APP.index("function " + end)]


@unittest.skipUnless(shutil.which("node"), "Node required to execute UI behavior")
class ProductViewTests(unittest.TestCase):
    def evaluate(self, expression, setup="", functions=PURE):
        result = subprocess.run(["node", "-e", functions + "\n" + setup + "\nconsole.log(JSON.stringify(" + expression + "));"],
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def board(self):
        stories = [{"id": "US-1", "epicId": "EPIC-A", "status": "ready", "priority": 2},
                   {"id": "US-2", "epicId": "EPIC-B", "status": "ready", "priority": 1},
                   {"id": "US-3", "epicId": "EPIC-A", "status": "done", "priority": 3}]
        return {"generatedAt": "one", "epics": [{"id": "LEGACY", "increments": [{"id": "INC-1"}]}],
                "storyBoard": {"version": 1, "configured": True, "valid": True, "storeSha256": HASH,
                               "stories": stories, "epics": [{"id": "EPIC-A"}, {"id": "EPIC-B"}], "deliveries": []},
                "productContext": {"version": 1, "configured": True, "valid": True,
                                   "source": ".aim/product-backlog.json", "storeSha256": HASH,
                                   "activeDeliveryId": None, "roles": [], "data": {"generatedAt": "one"},
                                   "counts": dict(intents=1, epics=2, openEpics=2, closedEpics=0, stories=3,
                                                  readyStories=2, doneStories=1, acceptedDeliveries=0)}}

    def delivery(self, status="planned"):
        return {"id": "DEL-1", "status": status, "scopeSha256": SCOPE,
                "goal": "Shared improvement", "stories": [{"id": "US-1"}, {"id": "US-2"}], "epics": []}

    def test_increment_coverage_matches_story_and_criterion_without_reordering(self):
        delivery = self.delivery("review")
        delivery["stories"] = [
            {"id": "US-2", "acceptanceCriteria": [{"id": "AC-1", "text": "Second Story"}]},
            {"id": "US-1", "acceptanceCriteria": [{"id": "AC-1", "text": "First Story"}, {"id": "AC-2", "text": "Other"}]}]
        delivery["criterionEvidence"] = [{"storyId": "US-1", "criterionId": "AC-1", "evidence": [{"path": "proof.md"}]}]
        detail = self.evaluate(f"productDeliveryDetail({json.dumps(delivery)})")
        self.assertEqual([story["id"] for story in detail["stories"]], ["US-2", "US-1"])
        self.assertEqual(detail["stories"][0]["criteria"][0]["evidence"], [])
        self.assertEqual(detail["stories"][1]["criteria"][0]["evidence"], [{"path": "proof.md"}])
        self.assertEqual((detail["evidencedCriteria"], detail["totalCriteria"]), (1, 3))
        delivery["criterionEvidence"] = []
        self.assertEqual(self.evaluate(f"productDeliveryDetail({json.dumps(delivery)}).evidencedCriteria"), 0)

    def test_approval_evidence_and_final_acceptance_are_distinct(self):
        delivery = self.delivery("acceptance")
        delivery["approval"] = {"path": "plan-authority.md"}
        delivery["acceptanceSha256"] = "c" * 64
        detail = self.evaluate(f"productDeliveryDetail({json.dumps(delivery)})")
        self.assertEqual(detail["plan"], "Approved scope")
        self.assertEqual(detail["acceptance"], "Awaiting user acceptance")
        delivery.update(status="blocked", blockedFrom="acceptance", reason="Needs corrections")
        detail = self.evaluate(f"productDeliveryDetail({json.dumps(delivery)})")
        self.assertEqual(detail["phase"], "acceptance")
        self.assertEqual(detail["acceptance"], "Not accepted · blocked")
        delivery.update(status="accepted", acceptance={"path": "user-acceptance.md"})
        self.assertEqual(self.evaluate(f"productDeliveryDetail({json.dumps(delivery)}).acceptance"), "Accepted by user")

    def test_cleanup_offer_handoff_does_not_authorize_deletion(self):
        functions = source_function("legacyCleanupPrompt(", "renderLegacyCleanup(")
        prompt = self.evaluate("legacyCleanupPrompt()", functions=functions)
        self.assertIn("Ask for my confirmation", prompt)
        self.assertIn("already explicitly authorized", prompt)
        self.assertIn("--expected-sha256", prompt)
        self.assertIn("all referenced evidence", prompt)

    def test_cleanup_offer_disappears_and_returns_to_product_after_cleanup(self):
        functions = source_function("renderLegacyCleanup(", "render(")
        setup = """
const nodes = {}; const $ = (id) => nodes[id] || (nodes[id] = {});
const legacy = {}; const document = {querySelector: () => legacy};
const state = {workspace:'legacy'};
renderLegacyCleanup({legacyCleanup:{legacyDetected:true}});
const before = {offer:!nodes['legacy-cleanup'].hidden, legacy:!legacy.hidden, workspace:state.workspace};
renderLegacyCleanup({legacyCleanup:{legacyDetected:false}});
"""
        result = self.evaluate("({before, after:{offer:!nodes['legacy-cleanup'].hidden, legacy:!legacy.hidden, workspace:state.workspace}})", setup, functions)
        self.assertEqual(result["before"], {"offer":True,"legacy":True,"workspace":"legacy"})
        self.assertEqual(result["after"], {"offer":False,"legacy":False,"workspace":"product"})

    def test_product_only_selection_is_cross_epic_and_excludes_done(self):
        board = json.dumps(self.board())
        result = self.evaluate(f"readyProductStories(productViewModel({board})).map(s => s.id)")
        self.assertEqual(result, ["US-2", "US-1"])
        request = {"kind": "plan", "storyIds": ["US-1", "US-2"], "goal": "Help both users"}
        prompt = self.evaluate(f"productHandoffPrompt({board}, {json.dumps(request)})")
        self.assertIn("planning proposal, not plan approval", prompt)
        self.assertIn("Have TDO propose", prompt)
        self.assertIn("PO-owned Epic intent and product priority", prompt)
        self.assertIn(HASH, prompt)
        self.assertIn("Reload .aim/product-backlog.json", prompt)
        self.assertIn("US-1", prompt)
        self.assertIn("US-2", prompt)
        self.assertNotIn("AIM_ACTION_ENVELOPE", prompt)
        request["storyIds"] = ["US-3"]
        self.assertEqual(self.evaluate(f"productHandoffPrompt({board}, {json.dumps(request)})"), "")

    def test_active_delivery_disables_planning_and_keeps_scope_in_handoff(self):
        board = self.board()
        board["storyBoard"]["deliveries"] = [self.delivery()]
        board["productContext"]["activeDeliveryId"] = "DEL-1"
        literal = json.dumps(board)
        self.assertEqual(self.evaluate(f"readyProductStories(productViewModel({literal}))"), [])
        prompt = self.evaluate(f"productHandoffPrompt({literal}, {{kind:'delivery',deliveryId:'DEL-1'}})")
        self.assertIn(SCOPE, prompt)
        self.assertIn(HASH, prompt)
        self.assertIn("does not approve a plan", prompt)
        self.assertIn("user-owned plan approval and final acceptance", prompt)

    def test_changed_or_invalid_store_clears_stale_selection(self):
        board = self.board()
        for previous in ("c" * 64, HASH):
            result = self.evaluate(f"reconcileProductSelection({json.dumps(board)}, {json.dumps(previous)}, ['US-1'])")
            self.assertEqual(result["ids"], ["US-1"] if previous == HASH else [])
            self.assertEqual(result["cleared"], previous != HASH)
        board["productContext"]["valid"] = False
        result = self.evaluate(f"reconcileProductSelection({json.dumps(board)}, '{HASH}', ['US-1'])")
        self.assertEqual(result["ids"], [])
        self.assertTrue(result["cleared"])

    def test_missing_malformed_or_mismatched_context_never_enables_actions(self):
        cases = [None, {"version": 1, "valid": False, "configured": True, "counts": None, "data": None},
                 {**self.board()["productContext"], "storeSha256": "c" * 64},
                 {**self.board()["productContext"], "counts": None}]
        for context in cases:
            with self.subTest(context=context):
                board = self.board()
                board["productContext"] = context
                literal = json.dumps(board)
                self.assertFalse(self.evaluate(f"productViewModel({literal}).available"))
                self.assertEqual(self.evaluate(f"productHandoffPrompt({literal},{{kind:'plan',storyIds:['US-1'],goal:'Test'}})"), "")

    def test_done_story_gets_new_need_without_refining_accepted_scope(self):
        prompt = self.evaluate(f"productHandoffPrompt({json.dumps(self.board())}, {{kind:'story',storyId:'US-3'}})")
        self.assertIn("new follow-up user need", prompt)
        self.assertIn("Preserve this accepted Story", prompt)
        self.assertIn("open Epic", prompt)
        self.assertIn("TDO may propose a new Story", prompt)
        self.assertIn("PO owns any new Epic and product priority", prompt)
        self.assertNotIn("Refine this user need", prompt)

    def test_refinement_handoff_assigns_story_to_tdo_without_authorizing_changes(self):
        board = self.board()
        before = json.dumps(board)
        prompt = self.evaluate(f"productHandoffPrompt({before}, {{kind:'story',storyId:'US-1'}})")
        self.assertIn("Have TDO refine", prompt)
        self.assertIn("PO-owned Epic intent and product priority", prompt)
        self.assertIn("Do not alter approved delivery scope", prompt)
        self.assertIn("Keep this discussion read only", prompt)
        self.assertIn(HASH, prompt)
        self.assertEqual(json.dumps(board), before)

    def test_blocked_checkpoint_keeps_previous_responsibility(self):
        self.assertEqual(self.evaluate("productCheckpoint({status:'blocked',blockedFrom:'review'})"), "Gate C · independent review")
        self.assertEqual(self.evaluate("productCheckpoint({status:'acceptance'})"), "Gate E · user acceptance pending")

    def test_evidence_names_disambiguate_distinct_paths_and_deduplicate_exact_refs(self):
        refs = [
            {"label": "Validation", "path": ".aim/analysis/aim4-press/validation.md"},
            {"label": "Validation", "path": ".aim/analysis/ui-scroll/validation.md"},
            {"label": "Review", "path": ".aim/review.md"},
            {"label": "Review", "path": ".aim/review.md"},
            {"label": "Plan", "path": ".aim/one/shared/plan.md"},
            {"label": "Plan", "path": ".aim/two/shared/plan.md"},
        ]
        labels = self.evaluate(f"labelProductEvidence({json.dumps(refs)}).map(ref => ref.displayLabel)")
        self.assertEqual(labels, ["Validation · aim4-press/validation.md", "Validation · ui-scroll/validation.md",
                                  "Review · review.md", "Plan · .aim/one/shared/plan.md", "Plan · .aim/two/shared/plan.md"])

    def test_signature_ignores_only_known_refresh_timestamps(self):
        functions = source_function("semanticBoardSignature(", "cardKey(")
        setup = "const board = " + json.dumps(self.board()) + "; board.deliveryData = {generatedAt:'one', history:[{acceptedAt:'real', evidence:'a'}]};"
        result = self.evaluate("(() => { const original = semanticBoardSignature(board); const copy = JSON.parse(JSON.stringify(board)); copy.generatedAt='two'; copy.deliveryData.generatedAt='two'; copy.productContext.data.generatedAt='two'; const refresh=semanticBoardSignature(copy); copy.deliveryData.history[0].acceptedAt='changed'; const acceptance=semanticBoardSignature(copy); copy.deliveryData.history[0].evidence='changed'; return {quiet:original===refresh,real:refresh!==acceptance,evidence:acceptance!==semanticBoardSignature(copy),untouched:board.generatedAt==='one'}; })()", setup, functions)
        self.assertEqual(result, {"quiet": True, "real": True, "evidence": True, "untouched": True})

    def test_rebuilt_goal_input_keeps_focus_and_text_selection(self):
        functions = source_function("captureFocus(", "captureViewport(")
        setup = """
const original = {id:'product-plan-goal', selectionStart:4, selectionEnd:11, selectionDirection:'backward'};
const document = {body:{}, activeElement:original};
const restored = {focus(options) {this.focusOptions=options;document.activeElement=this;},setSelectionRange(...args) {this.selection=args;}};
const $ = id => id === 'product-plan-goal' ? restored : null;
"""
        result = self.evaluate("(() => {const token=captureFocus();document.activeElement=document.body;restoreFocus(token);return {focused:document.activeElement===restored,options:restored.focusOptions,selection:restored.selection};})()", setup, functions)
        self.assertEqual(result, {"focused": True, "options": {"preventScroll": True}, "selection": [4, 11, "backward"]})

    def test_delivery_renderer_rebuild_preserves_summary_and_evidence_focus(self):
        board = self.board()
        delivery = self.delivery()
        delivery["stories"] = [{"id": "US-1", "epicId": "EPIC-A", "title": "Useful work",
                                "persona": "a user", "need": "help", "benefit": "value",
                                "acceptanceCriteria": [{"id": "AC-1", "text": "Works"}]}]
        delivery["validationEvidence"] = [{"path": ".aim/first/validation.md"}]
        board["storyBoard"]["deliveries"] = [delivery]
        board["productContext"]["activeDeliveryId"] = "DEL-1"
        functions = PRODUCT_SCRIPT + source_function("captureFocus(", "captureViewport(")
        # A small DOM models focus loss on removal; the production renderer creates
        # and replaces every node. No fixture supplies the identities under test.
        setup = """
class Node {
  constructor(tag) { this.tagName=tag; this.children=[]; this.dataset={}; this.id=''; }
  append(...children) { this.children.push(...children); }
  descendants() { return this.children.flatMap(child => [child,...child.descendants()]); }
  replaceChildren(...children) {
    if (this.descendants().includes(document.activeElement)) document.activeElement=document.body;
    this.children=children;
  }
  querySelectorAll(selector) {
    return this.descendants().filter(node => node.tagName==='details'
      && node.dataset.productDetail && (!selector.includes('[open]') || node.open));
  }
  setAttribute() {}
  addEventListener() {}
  focus(options) { document.activeElement=this; this.focusOptions=options; }
  get childElementCount() { return this.children.length; }
}
const document = {body:new Node('body')}; document.activeElement=document.body;
function el(tag, className='', text='') { const node=new Node(tag); node.className=className; node.textContent=text; return node; }
const roots = ['product-content','product-view-title','product-view-summary','product-notice'].map(id => {const n=el('div');n.id=id;return n;});
const $ = id => [...roots,...roots.flatMap(root => root.descendants())].find(node => node.id===id);
function statusLabel(status) {return status;}
function addFact() {}
""" + "const state={board:" + json.dumps(board) + ", view:'board', productDeliveryId:null};"
        expression = """(() => {
  const results=[];
  renderProductWorkspace(state.board);
  for (const select of [nodes => nodes.find(n => n.tagName==='summary'),
    nodes => nodes.filter(n => n.tagName==='summary')[1], nodes => nodes.find(n => n.tagName==='a')]) {
    $('product-content').querySelectorAll('details[data-product-detail]').forEach(n => n.open=true);
    const old=select($('product-content').descendants()); old.focus(); const token=captureFocus();
    state.board.storyBoard.deliveries[0].goal+=' updated';
    // A new same-basename link changes display labels and ordering, not identity.
    state.board.storyBoard.deliveries[0].validationEvidence.unshift({path:'.aim/new/validation.md'});
    renderProductWorkspace(state.board); const lost=document.activeElement===document.body;
    restoreFocus(token); const current=document.activeElement;
    results.push({lost,replaced:current!==old,identity:current.id===old.id,
      restored:current!==document.body,preventScroll:current.focusOptions?.preventScroll,
      expanded:$('product-content').querySelectorAll('details[open][data-product-detail]').length===2});
  }
  const token=captureFocus(); renderProductWorkspace(state.board);
  $('product-view-title').focus(); restoreFocus(token);
  const navigation=document.activeElement===$('product-view-title');
  $('product-content').descendants().find(n => n.tagName==='a').focus(); const removed=captureFocus();
  state.board.storyBoard.deliveries[0].validationEvidence=[];
  renderProductWorkspace(state.board); restoreFocus(removed);
  return {results,navigation,removed:document.activeElement===document.body};
})()"""
        result = self.evaluate(expression, setup, functions)
        self.assertEqual(result["results"], [dict(lost=True, replaced=True, identity=True,
                                               restored=True, preventScroll=True, expanded=True)] * 3)
        self.assertTrue(result["navigation"])
        self.assertTrue(result["removed"])

    def test_only_active_view_is_rendered(self):
        functions = PURE + source_function("renderView(", "renderNotices(")
        setup = """
const state = {workspace:'product',view:'stories'};
const calls = [];
const nodes = {};
const $ = id => nodes[id] || (nodes[id] = {});
const document = {querySelectorAll: () => []};
function renderStories() { calls.push('stories'); }
function renderProductWorkspace() { calls.push('product'); }
function renderDiscussion() { calls.push('discuss'); }
function renderData() { calls.push('data'); }
function renderPeople() { calls.push('legacyPeople'); }
function renderClosed() { calls.push('legacyClosed'); }
function renderKanban() { calls.push('legacyBoard'); }
function renderRecentDeliveries() { calls.push('legacyRecent'); }
function renderNotices() {}
function renderPortfolioControl() { calls.push('legacyPortfolio'); }
function renderPortfolioRun() {}
function renderPortfolioJourney() {}
function renderRoadmap() {}
function renderEpicRoster() {}
"""
        expression = "(() => {const board=" + json.dumps(self.board()) + "; renderView(board,[]); const story=calls.splice(0); state.view='discuss'; renderView(board,[]); const discussion=calls.splice(0); state.view='people'; renderView(board,[]); const people=calls.splice(0); state.workspace='legacy'; renderView(board,[]); return {story,discussion,people,legacy:calls};})()"
        self.assertEqual(self.evaluate(expression, setup, functions), {"story": ["stories"], "discussion": ["discuss"], "people": ["product"], "legacy": ["legacyPeople"]})

    def test_legacy_paused_or_invalid_precedes_ready_candidates(self):
        function = source_function("portfolioJourneyState(", "renderPortfolioJourney(")
        for status in ("paused", "invalid", "failed"):
            board = {"roadmap": {"configured": True, "valid": True, "eligibleCount": 3},
                     "portfolioRun": {"configured": True, "valid": status != "invalid", "status": status}}
            result = self.evaluate(f"portfolioJourneyState({json.dumps(board)})", functions=function)
            self.assertEqual(result["command"], "/aim status")
            self.assertNotIn("review", result["completed"])
        board = {"roadmap": {"configured": True, "valid": True, "eligibleCount": 2}}
        result = self.evaluate(f"portfolioJourneyState({json.dumps(board)})", functions=function)
        self.assertNotIn("review", result["completed"])


if __name__ == "__main__":
    unittest.main()
