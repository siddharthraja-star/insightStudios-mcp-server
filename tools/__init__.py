from . import containers, exec, logs, rca, docs

ALL_TOOLS = [
    containers.TOOL_DEF,
    logs.GET_LOGS_TOOL_DEF,
    logs.STREAM_LOGS_TOOL_DEF,
    logs.WAIT_AND_STREAM_TOOL_DEF,
    exec.TOOL_DEF,
    rca.RCA_TOOL_DEF,
    docs.EXPORT_DOCS_TOOL_DEF,
]

HANDLERS = {
    "list_containers": containers.handle,
    "get_container_logs": logs.handle_get_logs,
    "stream_container_logs": logs.handle_stream_logs,
    "wait_and_stream_logs": logs.handle_wait_and_stream,
    "exec_in_container": exec.handle,
    "analyze_and_write_rca": rca.handle_analyze_and_write_rca,
    "export_rca_docs": docs.handle_export_rca_docs,
}
