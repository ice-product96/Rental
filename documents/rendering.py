from django.template import Template, Context


class ContractRenderError(Exception):
    pass


def build_contract_context(*, our_entity, client, deal=None, contract_number='', contract_date=None):
    from types import SimpleNamespace

    contract = SimpleNamespace(number=contract_number, date=contract_date)
    return {
        'our': our_entity,
        'client': client,
        'deal': deal,
        'contract': contract,
    }


def render_contract_html(template_body, context_dict):
    try:
        tpl = Template(template_body)
        return tpl.render(Context(context_dict))
    except Exception as exc:
        raise ContractRenderError(str(exc)) from exc
