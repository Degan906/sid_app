# 🚗 SID - Sistema de Manutenção de Veículos

Este é um sistema leve feito com **Python + Streamlit** que permite cadastrar:

- 👤 Clientes
- 🚗 Veículos (associados aos clientes)
- 🔧 Manutenções (associadas aos veículos)

Todos os dados são salvos localmente em arquivos `.csv` e podem ser versionados via Git.

---

## 📦 Estrutura do Projeto

```
sid_app/
├── app.py                # Menu principal com Streamlit
├── modules/              # Módulos de cada funcionalidade
│   ├── clientes.py
│   ├── veiculos.py
│   └── manutencoes.py
├── data/                 # Arquivos CSV com os dados
│   ├── clientes.csv
│   ├── veiculos.csv
│   └── manutencoes.csv
├── README.md             # Este arquivo
└── .gitignore
```

---

## ▶️ Como executar localmente

1. **Clone o repositório:**

```bash
git clone https://github.com/seu-usuario/sid_app.git
cd sid_app
```

2. **Instale as dependências:**

Recomenda-se criar um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate    # Windows

pip install streamlit pandas
```

3. **Execute o sistema:**

```bash
streamlit run app.py
```

---

## 💾 Onde os dados ficam salvos?

Todos os dados ficam na pasta `data/`:

- `clientes.csv`
- `veiculos.csv`
- `manutencoes.csv`

Esses arquivos são gerados automaticamente.

---

## ✅ Funcionalidades atuais

- Cadastro e listagem de clientes
- Cadastro de veículos associados a clientes
- Cadastro de manutenções por veículo
- Interface responsiva via Streamlit

---

## 📌 Requisitos

- Python 3.8+
- Streamlit
- Pandas

---

## 📄 Licença

Este projeto é livre para uso e modificação.

---

## 🙋‍♂️ Autor

Desenvolvido por Henrique Degan e ChatGPT
