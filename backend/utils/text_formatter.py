def row_to_text_orm_weighted(row):
    provider = "The provider is " + str(row.provider) + "." or ''
    data = "The amount of data is " + str(row.data) or '' + ' ' + str(row.gb) or ''
    return (
        f"Provider: {' '.join([provider] * 4)}" ## Repeat 4 times for higher weighting in semantic embeddings
        f"Data: {' '.join([data] * 4)}, "
        f"Item: {row.item_name or ''}, "
        f"Region: {row.region or ''}, "
        f"Condition: {row.condition or ''}, "
        f"Channel: {row.channel or ''}, "
        f"Line Type: {row.line_type or ''}, "
        f"Promotion Price: {row.promotion_price or ''}, "
        f"Original Price: {row.original_price or ''}, "
        f"Overage Rate: {row.overage_rate or ''}, "
        f"Roaming: {row.roaming or ''}, "
        f"BYOD/Term: {row.byod_or_term or ''}, "
        f"Free LD: {row.free_ld or ''}, "
        f"Activation Fee: {row.activation_fee or ''}, "
        f"Promo start: {row.promo_start_date or ''}, "
        f"Promo end: {row.promo_end_date or ''}, "
        f"Code: {row.code or ''}, "
        f"Tier: {row.tier or ''}"
    )


def row_to_text_dict(row: dict):
    return (
        f"Item: {row.get('item_name', '')}, "
        f"Provider: {row.get('provider', '')}, "
        f"Region: {row.get('region', '')}, "
        f"Condition: {row.get('condition', '')}, "
        f"Channel: {row.get('channel', '')}, "
        f"Line Type: {row.get('line_type', '')}, "
        f"Promotion Price: {row.get('promotion_price', '')}, "
        f"Original Price: {row.get('original_price', '')}, "
        f"Overage Rate: {row.get('overage_rate', '')}, "
        f"Data: {row.get('data', '')}, "
        f"GB: {row.get('gb', '')}, "
        f"Roaming: {row.get('roaming', '')}, "
        f"BYOD/Term: {row.get('byod_or_term', '')}, "
        f"Free LD: {row.get('free_ld', '')}, "
        f"Activation Fee: {row.get('activation_fee', '')}, "
        f"Promo start: {row.get('promo_start_date', '')}, "
        f"Promo end: {row.get('promo_end_date', '')}, "
        f"Code: {row.get('code', '')}, "
        f"Tier: {row.get('tier', '')}"
    )


def row_to_text_obj(row):
    return (
        f"Item: {row['item_name'] or ''}, "
        f"Provider: {row['provider'] or ''}, "
        f"Region: {row['region'] or ''}, "
        f"Condition: {row['condition'] or ''}, "
        f"Channel: {row['channel'] or ''}, "
        f"Line Type: {row['line_type'] or ''}, "
        f"Promotion Price: {row['promotion_price'] or ''}, "
        f"Original Price: {row['original_price'] or ''}, "
        f"Overage Rate: {row['overage_rate'] or ''}, "
        f"Data: {row['data'] or ''}, "
        f"GB: {row['gb'] or ''}, "
        f"Roaming: {row['roaming'] or ''}, "
        f"BYOD/Term: {row['byod_or_term'] or ''}, "
        f"Free LD: {row['free_ld'] or ''}, "
        f"Activation Fee: {row['activation_fee'] or ''}, "
        f"Promo start: {row['promo_start_date'] or ''}, "
        f"Promo end: {row['promo_end_date'] or ''}, "
        f"Code: {row['code'] or ''}, "
        f"Tier: {row['tier'] or ''}"
    )

def row_to_text_dict_compressed(row: dict) -> str:
    return " | ".join([
        str(row.get('item_name', '') or ''),
        str(row.get('provider', '') or ''),
        str(row.get('region', '') or ''),
        str(row.get('condition', '') or ''),
        str(row.get('channel', '') or ''),
        str(row.get('line_type', '') or ''),
        str(row.get('promotion_price', '') or ''),
        str(row.get('original_price', '') or ''),
        str(row.get('overage_rate', '') or ''),
        str(row.get('data', '') or ''),
        str(row.get('gb', '') or ''),
        str(row.get('roaming', '') or ''),
        str(row.get('byod_or_term', '') or ''),
        str(row.get('free_ld', '') or ''),
        str(row.get('activation_fee', '') or ''),
        str(row.get('promo_start_date', '') or ''),
        str(row.get('promo_end_date', '') or ''),
        str(row.get('code', '') or ''),
        str(row.get('tier', '') or '')
    ])

def row_to_dict(row) -> dict:
    return {
        "item_name": row.item_name,
        "provider": row.provider,
        "region": row.region,
        "condition": row.condition,
        "channel": row.channel,
        "line_type": row.line_type,
        "promotion_price": row.promotion_price,
        "original_price": row.original_price,
        "overage_rate": row.overage_rate,
        "data": row.data,
        "roaming": row.roaming,
        "byod_or_term": row.byod_or_term,
        "free_ld": row.free_ld,
        "activation_fee": row.activation_fee,
        "promo_start_date": row.promo_start_date,
        "promo_end_date": row.promo_end_date,
        "code": row.code,
        "tier": row.tier
    }


