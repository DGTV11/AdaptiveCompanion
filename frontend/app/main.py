from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label


class LoginScreen(ModalScreen):
    """Login screen."""

    def compose(self) -> ComposeResult:
        with Grid(classes="form"):
            yield Label("Log in", classes="form-title")
            with Horizontal(classes="form-field"):
                yield Button("Username", disabled=True)
                self.username_input = Input(placeholder="username")
                yield self.username_input
            with Horizontal(classes="form-field"):
                yield Button("Password", disabled=True)
                self.password_input = Input(placeholder="password", password=True)
                yield self.password_input
            yield Button(
                "Log in", variant="primary", id="login-btn", classes="submit-btn"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            username = self.username_input.value
            password = self.password_input.value
            print(username, password)  # TODO: send request to backend
            # TODO: make sign in form


class AdaptiveCompanion(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("l", "login", "Log in")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("TEST")
        yield Footer()

    def action_login(self) -> None:
        self.push_screen(LoginScreen())


if __name__ == "__main__":
    app = AdaptiveCompanion()
    app.run()
