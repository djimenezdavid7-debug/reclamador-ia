import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hola Mundo - Test Flet"))

if __name__ == "__main__":
    ft.app(target=main, port=8081, view=ft.AppView.WEB_BROWSER)
