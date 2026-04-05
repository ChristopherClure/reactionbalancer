from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, ListView, ListItem, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual import on
from chempy import balance_stoichiometry
from chempy import Substance
import re


EXAMPLES = [
    "H2 + O2 -> H2O",
    "Fe + O2 -> Fe2O3",
    "C3H8 + O2 -> CO2 + H2O",
    "Al + HCl -> AlCl3 + H2",
    "KMnO4 + HCl -> KCl + MnCl2 + H2O + Cl2",
    "Ca3(PO4)2 + SiO2 + C -> CaSiO3 + P4 + CO",
    "Cr2O3 + Al -> Al2O3 + Cr",
    "CH4 + O2 -> CO2 + H2O",
]


_SUBSCRIPT_TABLE = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalize(formula: str) -> str:
    """Normalize unicode subscripts and hydrate dot notation to ASCII."""
    formula = formula.translate(_SUBSCRIPT_TABLE)
    # Expand hydrate dot: A·nB → A(B)n  (e.g. ZrOCl2·8H2O → ZrOCl2(H2O)8)
    if "·" in formula:
        base, hydrate = formula.split("·", 1)
        m = re.match(r"^(\d*)(.+)$", hydrate)
        if m:
            n, part = m.group(1) or "1", m.group(2)
            formula = f"{base}({part}){n}"
    return formula


def parse_equation(equation: str) -> tuple[set, set]:
    """Parse 'A + B -> C + D' into (reactants_set, products_set)."""
    arrow_re = re.compile(r"\s*->\s*|\s*→\s*|\s*=\s*")
    parts = arrow_re.split(equation, maxsplit=1)
    if len(parts) != 2:
        raise ValueError("Equation must contain '->' separating reactants and products.")
    reactants = {_normalize(s.strip()) for s in parts[0].split("+") if s.strip()}
    products = {_normalize(s.strip()) for s in parts[1].split("+") if s.strip()}
    if not reactants or not products:
        raise ValueError("Both sides of the equation must have at least one species.")
    return reactants, products


def format_side(species_dict: dict) -> str:
    """Format an ordered dict of {species: coeff} as a readable equation side."""
    parts = []
    for species, coeff in species_dict.items():
        if coeff == 1:
            parts.append(species)
        else:
            parts.append(f"{coeff} {species}")
    return " + ".join(parts)


def molar_masses(species: set) -> dict[str, float]:
    """Return {formula: molar_mass_g_per_mol} for each formula in species."""
    result = {}
    for formula in species:
        try:
            result[formula] = Substance.from_formula(formula).mass
        except Exception:
            pass
    return result


def balance(equation: str) -> tuple[str, dict[str, float]]:
    """Balance a chemical equation string; return (balanced_str, molar_masses_dict)."""
    reactants, products = parse_equation(equation)
    reac, prod = balance_stoichiometry(reactants, products)
    balanced = f"{format_side(reac)}  →  {format_side(prod)}"
    masses = molar_masses(reactants | products)
    return balanced, masses


HELP_TEXT = """\
[bold]Enter a chemical equation[/bold] using [cyan]+[/cyan] to separate species and [cyan]->[/cyan] to separate reactants from products.

[bold]Examples:[/bold]
  H2 + O2 -> H2O
  Fe + O2 -> Fe2O3
  CH4 + O2 -> CO2 + H2O

[bold]Tips:[/bold]
  • Subscripts are written as numbers: [cyan]H2O[/cyan], [cyan]C3H8[/cyan]
  • Parentheses supported: [cyan]Ca3(PO4)2[/cyan]
  • Press [cyan]Enter[/cyan] to balance, [cyan]Escape[/cyan] to clear
  • Click any example on the right to load it
  • Press [cyan]ctrl+q[/cyan] to quit\
"""


class HistoryItem(ListItem):
    def __init__(self, original: str, balanced: str) -> None:
        super().__init__()
        self.original = original
        self.balanced = balanced

    def compose(self) -> ComposeResult:
        yield Label(f"[dim]in:[/dim]  {self.original}")
        yield Label(f"[dim]out:[/dim] [green bold]{self.balanced}[/green bold]")


class ReactionBalancerApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #layout {
        height: 1fr;
    }

    #left-panel {
        width: 2fr;
        padding: 1 2;
    }

    #right-panel {
        width: 1fr;
        border-left: tall $primary-darken-2;
        padding: 1 2;
    }

    #input-row {
        height: auto;
        margin-bottom: 1;
    }

    #equation-input {
        width: 1fr;
    }

    #result-box {
        height: auto;
        min-height: 4;
        border: round $primary-darken-2;
        padding: 1 2;
        margin-bottom: 1;
        background: $surface-darken-1;
    }

    #help-box {
        height: auto;
        border: round $primary-darken-3;
        padding: 1 2;
        background: $surface-darken-2;
    }

    #history-label {
        text-style: bold;
        margin-bottom: 1;
    }

    #history-list {
        height: 1fr;
    }

    HistoryItem {
        padding: 0 1;
        border-bottom: dashed $primary-darken-3;
    }

    #examples-label {
        text-style: bold;
        margin-bottom: 1;
    }

    .example-item {
        padding: 0 1;
    }

    .example-item:hover {
        background: $primary-darken-2;
    }

    #result-label {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    TITLE = "Reaction Balancer"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "clear_input", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout"):
            with Vertical(id="left-panel"):
                with Horizontal(id="input-row"):
                    yield Input(
                        placeholder="e.g.  H2 + O2 -> H2O",
                        id="equation-input",
                    )
                with Static(id="result-box"):
                    yield Label(
                        "Enter an equation above and press [bold]Enter[/bold] to balance it.",
                        id="result-label",
                    )
                with ScrollableContainer(id="help-box"):
                    yield Static(HELP_TEXT)
            with Vertical(id="right-panel"):
                yield Label("Examples", id="examples-label")
                with ListView(id="examples-list"):
                    for ex in EXAMPLES:
                        item = ListItem(Label(ex, classes="example-item"))
                        item._example = ex
                        yield item
                yield Label("History", id="history-label")
                with ScrollableContainer(id="history-list"):
                    pass
        yield Footer()

    @on(Input.Submitted, "#equation-input")
    def on_submit(self, event: Input.Submitted) -> None:
        equation = event.value.strip()
        if not equation:
            return
        self._balance_and_show(equation)

    @on(ListView.Selected, "#examples-list")
    def on_example_selected(self, event: ListView.Selected) -> None:
        item = event.item
        example = getattr(item, "_example", None)
        if example:
            inp = self.query_one("#equation-input", Input)
            inp.value = example
            self._balance_and_show(example)

    def _balance_and_show(self, equation: str) -> None:
        result_label = self.query_one("#result-label", Label)
        try:
            balanced, masses = balance(equation)
            masses_text = "  ".join(
                f"[yellow]{f}[/yellow] [dim]{m:.2f} g/mol[/dim]"
                for f, m in sorted(masses.items())
            )
            result_label.update(
                f"[bold green]Balanced:[/bold green]\n\n"
                f"  [cyan]{balanced}[/cyan]\n\n"
                f"[bold]Molar masses:[/bold]  {masses_text}"
            )
            self._add_history(equation, balanced)
        except Exception as e:
            result_label.update(f"[bold red]Error:[/bold red] {e}")

    def _add_history(self, original: str, balanced: str) -> None:
        history_container = self.query_one("#history-list", ScrollableContainer)
        item = HistoryItem(original, balanced)
        history_container.mount(item)
        history_container.scroll_end(animate=False)

    def action_clear_input(self) -> None:
        inp = self.query_one("#equation-input", Input)
        inp.value = ""
        inp.focus()


def main():
    ReactionBalancerApp().run()


if __name__ == "__main__":
    main()
