from typing import Union, List, Optional

class QueryBuilder:
    @staticmethod
    def build_dept_where_clause(
        code_dept: Union[str, List[str], None] = None,
        column_name: str = "codeCommuneEtablissement",
        base_conditions: Optional[List[str]] = None
    ) -> str:
        conditions = list(base_conditions) if base_conditions else []
        
        if code_dept:
            depts = [code_dept] if isinstance(code_dept, str) else code_dept
            depts_str = ", ".join(f"'{d}'" for d in depts)
            conditions.append(f"LEFT({column_name}, 2) IN ({depts_str})")
        
        if not conditions:
            return ""
        
        return "WHERE " + " AND ".join(conditions)