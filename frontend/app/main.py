import requests
from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.reactive import reactive
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
            response = requests.post(
                "http://backend:5556/token",
                data={
                    "username": self.username_input.value,
                    "password": self.password_input.value,
                },
            )
            if response.status_code != 200:
                raise Exception("TODO: Incorrect username or password error")

            self.dismiss(response.json()["access_token"])


class AdaptiveCompanion(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("l", "login", "Log in")]

    headers = reactive(dict)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("TEST")
        yield Footer()

    def action_login(self) -> None:
        def update_access_token(access_token: str):
            self.headers["Authorization"] = f"Bearer {access_token}"

        self.push_screen(LoginScreen(), update_access_token)


if __name__ == "__main__":
    app = AdaptiveCompanion()
    app.run()
