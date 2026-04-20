Yandex AI Studio Agents Integration for Open WebUI
==================================================

This manifold pipe is allowing to use agents from https://ai.yandex-team.ru/ service.

1) Create an agent at https://ai.yandex-team.ru/

2) Get an API Key at `https://aistudio.yandex.ru/platform/folders/<your_folder_id>/access`

3) Import this pipe to your Open WebUI.

4) Setup Valves: "Yandex Cloud Api Key" from step 2, "Yandex Cloud Folder Id", Agent Ids
   from step 1 (could be one or more with comma), "Agent Names" for cleaner agent names in
   WebUI (optional)

5) PROFIT!

6) In case you want to use agent with code interpreteur, there are few extra steps:

  * You need to find a model at /admin/settings/models Open WebUI admin interface,
    corresponding to selected agent.

  * You need to turn off the "File Context" in model settings to make Open WebUI not to
    attach RAG context to user messages. In this case, this pipe code will attach this files
    to your request, otherwise all files will be used only for Open WebUI RAG purproses and will
    not be used for code interpretation.

  * Additionally, you could also go to /admin/settings/documents WebUI page and turn on
    "Bypass Embedding and Retrieval" to increase speed of attaching files to WebUI.


Support
=======

At this point of early development, all support is provided via
https://github.com/yandex-cloud/yandex-ai-studio-sdk/issues
