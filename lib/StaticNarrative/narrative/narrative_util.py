from installed_clients.WorkspaceClient import Workspace
from installed_clients.baseclient import ServerError
from ..exceptions import WorkspaceError
from typing import Dict
# from .updater import update_narrative
from StaticNarrative.narrative_ref import NarrativeRef
import time

NARRATIVE_TYPE = "KBaseNarrative.Narrative"


def read_narrative(ref: NarrativeRef, ws_client: Workspace) -> Dict:
    """
    Fetches a Narrative and its object info from the Workspace
    If content is False, this only returns the Narrative's info
    and metadata, otherwise, it returns the whole workspace object.

    This is mainly a wrapper around Workspace.get_objects2(), except that
    it always returns a dict. If content is False, it returns a dict
    containing a single key: 'info', with the object info and, optionally,
    metadata.

    Can the following errors:
        ValueError (if ref isn't a Narrative object),
        WorkspaceError if there's a Workspace issue (ref isn't valid, or token isn't valid)

    :param ref: a NarrativeRef
    :param content: if True, returns the narrative document, otherwise just the metadata
    :param include_metadata: if True, includes the object metadata when returning
    """
    try:
        nar_data = ws_client.get_objects2({'objects': [{'ref': str(ref)}]})
        nar = nar_data['data'][0]
        _validate_nar_type(nar['info'][2], ref)
        # nar['data'] = update_narrative(nar['data'])
        return nar['data']
    except ServerError as err:
        raise WorkspaceError(err, ref.wsid)


def _validate_nar_type(t: str, ref: NarrativeRef):
    if not t.startswith(NARRATIVE_TYPE):
        err = "Expected a Narrative object"
        if ref is not None:
            err += f" with reference {str(ref)}"
        err += f", got a {t}"
        raise ValueError(err)


def save_narrative_url(config: Dict[str, str], token: str, ref: NarrativeRef, url: str) -> None:
    """
    Updates the Narrative workspace metadata with info about the new Static Narrative.
    Creates (or updates) metadata keys:
    static_narrative: narrative url
    static_narrative_ver: int, the version
    static_narrative_saved: int, ms since epoch saved
    If it fails, will throw a WorkspaceError
    :param ref: the NarrativeRef for the Narrative that was made static
    :param url: the url string that was saved (should really just be the path, not the full url,
        something like /123/4 instead of ci.kbase.us/n/123/4)
    """
    new_meta = {
        "static_narrative": url,
        "static_narrative_ver": str(ref.ver),
        "static_narrative_saved": str(int(time.time()*1000))
    }
    ws_client = Workspace(url=config["workspace-url"], token=token)
    try:
        ws_client.alter_workspace_metadata({"wsi": {"id": ref.wsid}, "new": new_meta})
    except ServerError as err:
        raise WorkspaceError(err, ref.wsid)