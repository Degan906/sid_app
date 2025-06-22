import requests
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.table import Table
from rich import box
from openpyxl import Workbook
import os
import platform

# Configurações da API do Jira
JIRA_URL = "https://hcdconsultoria.atlassian.net/rest/api/2"
JIRA_USERNAME = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"

console = Console()

def get_downloads_folder():
    home = os.path.expanduser("~")
    downloads_path = os.path.join(home, "Downloads")
    if not os.path.exists(downloads_path):
        try:
            os.makedirs(downloads_path)
            console.print(f"[green]✓ Pasta criada: {downloads_path}[/green]")
        except Exception as e:
            console.print(f"[red]Erro ao criar pasta Downloads: {e}[/red]")
            downloads_path = home
    return downloads_path

def get_all_fields():
    url = f"{JIRA_URL}/field"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
    try:
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Erro ao acessar a API do Jira: {e}[/red]")
        return None

def get_custom_field_metadata():
    url = "https://carboncars.atlassian.net/rest/scriptrunner/latest/custom/rest/custom-fields-metadata"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
    try:
        response = requests.get(url, headers=headers, auth=auth, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            console.print(f"[yellow]⚠️ Falha ao acessar endpoint customizado. Status: {response.status_code}[/yellow]")
            return []
    except Exception as e:
        console.print(f"[red]Erro ao conectar ao endpoint customizado: {e}[/red]")
        return []

def get_all_statuses():
    url = f"{JIRA_URL}/status"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
    try:
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Erro ao buscar status do Jira: {e}[/red]")
        return []

def get_fields_by_project_and_issuetype(project_key, issue_type_name):
    url = f"{JIRA_URL.replace('/rest/api/2', '')}/rest/api/2/issue/createmeta"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
    params = {
        "projectKeys": project_key,
        "issuetypeNames": issue_type_name,
        "expand": "projects.issuetypes.fields"
    }
    try:
        response = requests.get(url, headers=headers, auth=auth, params=params)
        response.raise_for_status()
        data = response.json()
        fields = []
        for project in data.get("projects", []):
            for issuetype in project.get("issuetypes", []):
                for field_id, field_info in issuetype.get("fields", {}).items():
                    fields.append({
                        "id": field_id,
                        "name": field_info.get("name", "N/A"),
                        "required": field_info.get("required", False),
                        "type": field_info.get("schema", {}).get("type", "N/A")
                    })
        return fields
    except Exception as e:
        console.print(f"[red]Erro ao buscar campos por projeto e tipo de issue: {e}[/red]")
        return []

def display_fields_table_paginated(fields, title="Campos do Jira", page_size=50):
    if not fields:
        console.print("[yellow]⚠️ Nenhum campo encontrado.[/yellow]")
        return
    total = len(fields)
    pages = (total + page_size - 1) // page_size
    current_page = 1
    while True:
        start = (current_page - 1) * page_size
        end = start + page_size
        page_items = fields[start:end]
        table = Table(title=f"[bold]{title} - Página {current_page}/{pages}[/bold]", box=box.ROUNDED, header_style="bold magenta", show_lines=True)
        table.add_column("Nº", justify="center", style="dim")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Nome", style="green")
        table.add_column("Tipo", style="yellow")
        table.add_column("Personalizado", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Criado em", style="dim")
        table.add_column("Última atualização", style="dim")
        table.add_column("Criador", style="blue")
        for idx, field in enumerate(page_items, start=start + 1):
            status = "✅ Ativo"
            if field.get('isHidden', False) or field.get('isDeprecated', False):
                status = "❌ Inativo"
            table.add_row(
                str(idx),
                field.get('id', 'N/A'),
                field.get('name', 'N/A'),
                field.get('schema', {}).get('type', 'N/A'),
                "✅" if field.get('custom', False) else "❌",
                status,
                field.get('created', 'N/A'),
                field.get('updated', 'N/A'),
                field.get('creator', 'N/A')
            )
        console.clear()
        console.print(table)
        console.print("\n[bold cyan]Controles:[/bold cyan] [P]rimeira | [A]nterior | [N]ext | [S]air")
        nav = input("Digite sua opção: ").strip().lower()
        if nav == "s": break
        elif nav == "p": current_page = 1
        elif nav == "a" and current_page > 1: current_page -= 1
        elif nav == "n" and current_page < pages: current_page += 1
        else: console.print("[red]Opção inválida![/red]")

def main():
    console.print("[bold blue]🔍 Bem-vindo ao Gerenciador de Campos do Jira[/bold blue]\n")
    fields = get_all_fields()
    if not fields:
        console.print("[red]Não foi possível obter os campos do Jira.[/red]")
        return
    metadata_list = get_custom_field_metadata()
    metadata_dict = {item['id']: item for item in metadata_list}
    processed_fields = []
    for field in fields:
        meta = metadata_dict.get(field.get('id'), {})
        processed_fields.append({
            'id': field.get('id'),
            'name': field.get('name'),
            'custom': field.get('custom', False),
            'schema': field.get('schema', {}),
            'isHidden': field.get('isHidden', False),
            'isDeprecated': field.get('isDeprecated', False),
            'created': meta.get('created', 'N/A'),
            'updated': meta.get('updated', 'N/A'),
            'creator': meta.get('creator', 'N/A')
        })

    while True:
        console.print("\n[bold cyan]Escolha uma opção:[/bold cyan]")
        console.print("1 - Consultar base geral")
        console.print("2 - Consultar um campo específico")
        console.print("3 - Consultar por tipo de campo")
        console.print("4 - Consultar status")
        console.print("5 - Consultar campos por Projeto e Tipo de Issue")
        choice = input("Digite 1, 2, 3, 4 ou 5: ").strip()
        if choice == "1":
            custom_fields = [f for f in processed_fields if f['custom']]
            standard_fields = [f for f in processed_fields if not f['custom']]
            console.print("\n[bold green] Campos Personalizados [/bold green]")
            display_fields_table_paginated(custom_fields, "Campos Personalizados (Custom Fields)")
            console.print("\n[bold yellow] Campos Padrão [/bold yellow]")
            display_fields_table_paginated(standard_fields, "Campos Padrão (Standard Fields)")
        elif choice == "2":
            search_term = input("Digite o nome ou ID do campo: ").strip().lower()
            found = [f for f in processed_fields if search_term in f.get('name', '').lower() or search_term == f.get('id', '')]
            if found:
                display_fields_table_paginated(found, f"Resultado da Busca por '{search_term}'")
            else:
                console.print("[yellow]⚠️ Nenhum campo encontrado com esse termo.[/yellow]")
        elif choice == "3":
            types = set()
            for field in processed_fields:
                t = field.get('schema', {}).get('type', 'N/A')
                if t != 'N/A':
                    types.add(t)
            types = sorted(types)
            for i, t in enumerate(types, 1):
                console.print(f"{i} - {t}")
            try:
                idx = int(input("Digite o número do tipo: ")) - 1
                if 0 <= idx < len(types):
                    tipo = types[idx]
                    filtrados = [f for f in processed_fields if f.get('schema', {}).get('type') == tipo]
                    display_fields_table_paginated(filtrados, f"Campos do tipo '{tipo}'")
                else:
                    console.print("[red]Índice inválido.[/red]")
            except:
                console.print("[red]Valor inválido.[/red]")
        elif choice == "4":
            statuses = get_all_statuses()
            search_term = input("Filtrar por nome (Enter para todos): ").strip().lower()
            if search_term:
                statuses = [s for s in statuses if search_term in s.get("name", "").lower()]
            table = Table(title="Status do Jira", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Nome", style="green")
            table.add_column("Descrição", style="yellow")
            table.add_column("Categoria", style="blue")
            for s in statuses:
                table.add_row(
                    s.get('id', 'N/A'),
                    s.get('name', 'N/A'),
                    s.get('description', '—'),
                    s.get('statusCategory', {}).get('name', 'N/A')
                )
            console.print(table)
        elif choice == "5":
            project_key = input("Digite a chave do projeto (ex: AP): ").strip()
            issue_type = input("Digite o nome do tipo de issue (ex: Tarefa): ").strip()
            campos = get_fields_by_project_and_issuetype(project_key, issue_type)
            if campos:
                table = Table(title=f"Campos para {project_key} - {issue_type}", box=box.ROUNDED)
                table.add_column("Nº", justify="center")
                table.add_column("ID", style="cyan")
                table.add_column("Nome", style="green")
                table.add_column("Tipo", style="yellow")
                table.add_column("Obrigatório", justify="center")
                for idx, campo in enumerate(campos, 1):
                    table.add_row(
                        str(idx),
                        campo["id"],
                        campo["name"],
                        campo["type"],
                        "✅" if campo["required"] else "❌"
                    )
                console.print(table)
            else:
                console.print("[yellow]⚠️ Nenhum campo retornado para esse projeto e tipo de issue.[/yellow]")
        else:
            console.print("[red]Opção inválida![/red]")
            continue
        repetir = input("\nDeseja realizar outra consulta? (S/N): ").strip().lower()
        if repetir != "s":
            break
    console.print("[bold green]👋 Obrigado por usar o gerenciador de campos do Jira![/bold green]")

if __name__ == "__main__":
    main()
