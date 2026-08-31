"""
Utilitários de Datas e Horários - SitiPet
Tratamento de formatos de data brasileiros, cálculo de diárias e alertas de agenda.
"""

from datetime import datetime, date, time, timedelta

MESES_PT_BR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

MESES_REVERSO = {nome: num for num, nome in MESES_PT_BR.items()}

def get_today_date() -> date:
    """Retorna a data atual."""
    return date.today()

def get_today_date_str() -> str:
    """Retorna a data atual no formato YYYY-MM-DD."""
    return date.today().strftime("%Y-%m-%d")

def get_now_time_str() -> str:
    """Retorna a hora atual no formato HH:MM."""
    return datetime.now().strftime("%H:%M")

def parse_date(date_val) -> date:
    """Converte string ou date para objeto datetime.date."""
    if isinstance(date_val, (date, datetime)):
        return date_val if isinstance(date_val, date) else date_val.date()
    if isinstance(date_val, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_val.strip(), fmt).date()
            except ValueError:
                continue
    return date.today()

def format_date_br(date_val) -> str:
    """Formata qualquer data para DD/MM/YYYY."""
    d = parse_date(date_val)
    return d.strftime("%d/%m/%Y")

def calc_dias_hospedagem(data_entrada, data_saida) -> int:
    """
    Calcula a quantidade de diárias entre duas datas.
    Se a data de saída for igual à data de entrada, considera 1 diária (day-use).
    """
    d_ent = parse_date(data_entrada)
    d_sai = parse_date(data_saida)
    
    diff = (d_sai - d_ent).days
    return max(1, diff)

def calcular_status_alerta_horario(data_agendamento, horario_str: str, status_atual: str) -> dict:
    """
    Avalia a proximidade do horário do atendimento para gerar alertas visuais.
    Retorna dicionário com:
    - badge_label: texto do status
    - cor: 'green', 'orange', 'red', 'blue', 'gray'
    - icon: emoji representativo
    - is_atrasado: bool
    - is_em_breve: bool
    """
    if status_atual in ["Finalizado", "Concluído"]:
        return {
            "badge_label": "Finalizado",
            "cor": "#10b981", # Verde
            "icon": "✅",
            "is_atrasado": False,
            "is_em_breve": False,
            "mensagem": "Atendimento concluído"
        }
    if status_atual == "Cancelado":
        return {
            "badge_label": "Cancelado",
            "cor": "#94a3b8", # Cinza
            "icon": "❌",
            "is_atrasado": False,
            "is_em_breve": False,
            "mensagem": "Atendimento cancelado"
        }
    if status_atual == "Em atendimento":
        return {
            "badge_label": "Em atendimento",
            "cor": "#3b82f6", # Azul
            "icon": "✂️",
            "is_atrasado": False,
            "is_em_breve": False,
            "mensagem": "Pet sendo atendido no momento"
        }

    d_agend = parse_date(data_agendamento)
    d_hoje = date.today()

    if d_agend < d_hoje:
        return {
            "badge_label": "Pendente (Passado)",
            "cor": "#ef4444",
            "icon": "⚠️",
            "is_atrasado": True,
            "is_em_breve": False,
            "mensagem": "Data anterior e não finalizado"
        }
    elif d_agend > d_hoje:
        return {
            "badge_label": status_atual or "Agendado",
            "cor": "#6366f1", # Roxo
            "icon": "📅",
            "is_atrasado": False,
            "is_em_breve": False,
            "mensagem": f"Agendado para {format_date_br(d_agend)}"
        }

    # Atendimento é HOJE: checar horários
    try:
        if isinstance(horario_str, str) and ":" in horario_str:
            partes = horario_str.strip().split(":")
            hora = int(partes[0])
            minuto = int(partes[1][:2])
        elif isinstance(horario_str, time):
            hora, minuto = horario_str.hour, horario_str.minute
        else:
            hora, minuto = 12, 0
    except Exception:
        hora, minuto = 12, 0

    agora = datetime.now()
    dt_agendamento = datetime.combine(d_hoje, time(hora, minuto))
    diff_minutos = (dt_agendamento - agora).total_seconds() / 60.0

    if diff_minutos < -15:
        return {
            "badge_label": "Atrasado",
            "cor": "#ef4444", # Vermelho
            "icon": "🚨",
            "is_atrasado": True,
            "is_em_breve": False,
            "mensagem": f"Atrasado há {abs(int(diff_minutos))} min"
        }
    elif -15 <= diff_minutos <= 45:
        return {
            "badge_label": "Em breve (Próximo)",
            "cor": "#f59e0b", # Amarelo/Laranja
            "icon": "⏰",
            "is_atrasado": False,
            "is_em_breve": True,
            "mensagem": f"Faltam {max(0, int(diff_minutos))} min" if diff_minutos > 0 else "Horário do atendimento!"
        }
    else:
        return {
            "badge_label": status_atual or "Agendado",
            "cor": "#10b981", # Verde
            "icon": "🟢",
            "is_atrasado": False,
            "is_em_breve": False,
            "mensagem": f"Hoje às {horario_str}"
        }

def get_meses_pt_br() -> dict:
    return MESES_PT_BR

def get_meses_nomes() -> list:
    return list(MESES_PT_BR.values())

def get_anos_disponiveis(start_year: int = 2024, end_year: int = 2032) -> list:
    return list(range(start_year, end_year + 1))

def mes_nome_para_numero(nome_mes: str) -> int:
    return MESES_REVERSO.get(nome_mes, datetime.now().month)

def mes_numero_para_nome(num_mes: int) -> str:
    return MESES_PT_BR.get(num_mes, "Janeiro")
