from argparse import ArgumentParser
from todoist_api_python.api import TodoistAPI
from dateutil import parser as dateparser
from json import dump, load


def construct_list_of_collection_projects(argument_str):
    cp_list = []
    if type(argument_str) is str:
        for collection_project_str in argument_str.split(','):
            cp_list.append(' '.join(collection_project_str.split('__')))
    return cp_list


def get_project_list(api, cp_list):
    cp = {}
    rp = {}
    rp_list = []
    projects = {}
    try:
        tdi_projects = api.get_projects()
        for p in tdi_projects:
            if p.name in cp_list:
                cp[p.id] = p
            else:
                projects["TDI_project_" + p.id] = {
                    "id": "TDI_project_" + p.id,
                    "tdi_id": p.id,
                    "tdi_project_object": p,
                    "tdi_task_object": None,
                    "title": p.name,
                    "taskIds": [],
                    "noteIds": [],
                    "isHiddenFromMenu": False,
                    "isArchived": False,
                    "backlogTaskIds": [],
                    "workStart": {},
                    "workEnd": {},
                    "breakTime": {},
                    "breakNr": {}
                }
                rp_list.append(p.name)
                rp[p.id] = p
        tasks = api.get_tasks()
        for task in tasks:
            if task.project_id in cp.keys() and task.parent_id is None:
                projects["TDI_subtask_project_" + task.project_id + '_' + task.id] = {
                    "id": "TDI_subtask_project_" + task.project_id + '_' + task.id,
                    "tdi_id": task.id,
                    "tdi_project_object": cp[task.project_id],
                    "tdi_task_object": task,
                    "title": task.content,
                    "taskIds": [],
                    "noteIds": [],
                    "isHiddenFromMenu": False,
                    "isArchived": False,
                    "backlogTaskIds": [],
                    "workStart": {},
                    "workEnd": {},
                    "breakTime": {},
                    "breakNr": {}
                }
    except Exception as error:
        print(error)
    return projects


def task_due_to_timestamp(task):
    if task.due is None:
        return None
    else:
        if task.due.datetime is not None:
            return round(dateparser.parse(task.due.datetime).timestamp())
        else:
            return round(dateparser.parse(task.due.date).timestamp())


def find_project_by_task_id(projects, task_id):
    for key in projects.keys():
        if projects[key]["tdi_task_object"] is None:
            continue
        if task_id == projects[key]["tdi_task_object"].id:
            return key


def find_project_id(projects, project_id):
    for key in projects.keys():
        if project_id == projects[key]["tdi_project_object"].id:
            return key


def get_all_active_tasks(api, projects, tags_by_name):
    try:
        tasks = api.get_tasks()
    except Exception as error:
        print(error)
        return
    regular_subtasks = []
    all_tasks = {}
    for task in tasks:
        task_project = None
        if task.parent_id is not None:
            task_project = find_project_by_task_id(projects, task.parent_id)
            if task_project is None:
                regular_subtasks.append(task)
                task_project = find_project_id(projects, task.project_id)
        dt = dateparser.parse(task.created_at)
        sp_task = {
            "id": "TDI_task_" + task.id,
            "projectId": find_project_id(projects, task.project_id) if task.parent_id is None else task_project,
            "parentId": None,
            "subTaskIds": [],
            "created": round(dt.timestamp()),
            "title": task.content,
            "notes": task.description,
            "tagIds": [tags_by_name[label] for label in task.labels if label in tags_by_name.keys()],
            "plannedAt": task_due_to_timestamp(task),
            "isDone": False,
            "doneOn": None,
            "timeSpent": 0,
            "timeEstimate": 0,
            "reminderId": None,
            "repeatCfgId": None,
            "attachments": [],
            "issueId": None,
            "issuePoints": None,
            "issueType": None,
            "issueAttachmentNr": None,
            "issueLastUpdated": None,
            "issueWasUpdated": None,
            "_showSubTasksMode": 2
        }
        all_tasks[sp_task["id"]] = sp_task
    for task in regular_subtasks:
        all_tasks["TDI_task_" + task.id]["parentId"] = "TDI_task_" + task.parent_id
        all_tasks["TDI_task_" + task.parent_id]["subTaskIds"].append("TDI_task_" + task.id)
    return all_tasks


def patch_config(config, projects, notes, tasks):
    for project_key in projects.keys():
        if project_key not in config["project"]["ids"]:
            config["project"]["ids"].append(project_key)
            with open("standard_project_fields.json", 'r') as spfjf:
                config["project"]["entities"][project_key] = load(spfjf)
        for key in projects[project_key].keys():
            if not key.startswith("tdi_"):
                config["project"]["entities"][project_key][key] = projects[project_key][key]
    for note_key in notes.keys():
        if note_key not in config["note"]["ids"]:
            config["note"]["ids"].append(note_key)
            config["note"]["entities"][note_key] = {}
        for key in notes[note_key].keys():
            if not key.startswith("tdi_"):
                config["note"]["entities"][note_key][key] = notes[note_key][key]
    for task_key in tasks.keys():
        if task_key not in config["task"]["ids"]:
            config["task"]["ids"].append(task_key)
            config["task"]["entities"][task_key] = {}
        for key in tasks[task_key].keys():
            if not key.startswith("tdi_"):
                config["task"]["entities"][task_key][key] = tasks[task_key][key]
    return config


def main():
    parser = ArgumentParser()
    parser.add_argument('--todoist_api_token', type=str,
                        help="The API token for ToDoIst." +
                             "You find it in the developer settings under sync in the ToDoIst webapp.")
    parser.add_argument('--super_productivity_json_file', type=str,
                        help="The backup file from Super Productivity.")
    parser.add_argument('--collection_projects', type=str,
                        help="Comma separated list of projects in ToDoIst used as GTD projects with subtasks. " +
                             "Double Underscores are replaced with spaces")
    args = parser.parse_args()
    if args.super_productivity_json_file is None:
        config = {}
    else:
        with open(args.super_productivity_json_file, 'r') as spbf:
            config = load(spbf)
    cp_list = construct_list_of_collection_projects(args.collection_projects)
    api = TodoistAPI(args.todoist_api_token)
    projects = get_project_list(api, cp_list)
    tags_by_name = {}
    if 'tag' in config and 'entities' in config['tag']:
        for x in config['tag']['entities']:
            tags_by_name[config['tag']['entities'][x]['title']] = x
    notes = {}
    for project_key in projects.keys():
        if projects[project_key]["tdi_task_object"] is not None and \
                len(projects[project_key]["tdi_task_object"].description) > 0:
            notes["TDI_note_from_task_description_" + projects[project_key]["tdi_task_object"].id] = {
                "id": "TDI_note_from_task_description_" + projects[project_key]["tdi_task_object"].id,
                "projectId": project_key,
                "content": projects[project_key]["tdi_task_object"].description,
                "isPinnedToToday": False,
                "created": round(dateparser.parse(projects[project_key]["tdi_task_object"].created_at).timestamp()),
                "modified": round(dateparser.parse(projects[project_key]["tdi_task_object"].created_at).timestamp())
            }
            projects[project_key]["noteIds"].append(
                notes["TDI_note_from_task_description_" + projects[project_key]["tdi_task_object"].id])
    tasks = get_all_active_tasks(api, projects, tags_by_name)
    for task_key in tasks.keys():
        projects[tasks[task_key]["projectId"]]["taskIds"].append(task_key)
    config = patch_config(config, projects, notes, tasks)
    with open("super_productivity_updated_backup_file.json", 'w') as of:
        dump(config, of)


if __name__ == '__main__':
    main()
