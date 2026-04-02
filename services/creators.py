"""
Creator merge/deduplication logic.
"""

from sqlalchemy.orm import Session

from models import Creator, CreatorRole


def merge_creators(
    db: Session,
    source_id: str,
    target_id: str,
) -> tuple[Creator, int]:
    """
    Merge source creator into target creator.

    Transfers all roles from source to target, merges aliases,
    and deletes the source creator.

    Returns (updated target creator, number of roles transferred).
    """
    source = db.query(Creator).filter(Creator.creator_id == source_id).first()
    target = db.query(Creator).filter(Creator.creator_id == target_id).first()

    if not source or not target:
        raise ValueError("Source or target creator not found")

    # Transfer all creator roles from source to target
    source_roles = (
        db.query(CreatorRole)
        .filter(CreatorRole.creator_id == source_id)
        .all()
    )
    roles_transferred = len(source_roles)
    for role in source_roles:
        role.creator_id = target_id

    # Merge aliases: combine both alias lists + source display_name
    target_aliases = list(target.aliases or [])
    source_aliases = list(source.aliases or [])

    # Add source's display_name as an alias if different from target
    if source.display_name != target.display_name:
        source_aliases.append(source.display_name)

    for alias in source_aliases:
        if alias not in target_aliases:
            target_aliases.append(alias)

    target.aliases = target_aliases if target_aliases else None

    # Delete the source creator (roles already transferred)
    db.delete(source)

    return target, roles_transferred
