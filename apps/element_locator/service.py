"""YAML serialization utility."""


def simple_yaml_dump(obj, indent=0) -> str:
    """Serialize Python dict/list to YAML string without PyYAML dependency."""
    lines = []
    prefix = "  " * indent

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(simple_yaml_dump(v, indent + 1))
            elif isinstance(v, str):
                if "\n" in v or "'" in v or ":" in v:
                    lines.append(f'{prefix}{k}: "{v}"')
                else:
                    lines.append(f"{prefix}{k}: {v}")
            elif v is None:
                lines.append(f"{prefix}{k}:")
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                lines.append(f"{prefix}- ")
                for dk, dv in item.items():
                    if isinstance(dv, dict):
                        lines.append(f"{prefix}  {dk}:")
                        lines.append(simple_yaml_dump(dv, indent + 2))
                    elif isinstance(dv, str):
                        if "\n" in dv or "'" in dv:
                            lines.append(f'{prefix}  {dk}: "{dv}"')
                        else:
                            lines.append(f"{prefix}  {dk}: {dv}")
                    else:
                        lines.append(f"{prefix}  {dk}: {dv}")
            elif isinstance(item, str):
                lines.append(f"{prefix}- {item}")
            else:
                lines.append(f"{prefix}- {item}")

    return "\n".join(lines)
