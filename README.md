# ToDoIst_to_SuperProductivity
Command line tool to load tasks from ToDoIst and convert them to a format importable by SuperProductivity.

>[!WARNING]
> At the moment Super Productivity displays a unreadable warning when importing the backup file. 
> However the information is there. Uns this at your own risk!


Install the dependencies with `pipenv install`.

Start Super Productivity, go to "Settings" -> „Sync“ and export a Backup file.

Run the script like this:
```shell
pipenv run python create_sp_backup_file.py --todoist_api_token 1234567890abcdefghijklmnopqrstuvwxyz1234567890 --super_productivity_json_file /home/pina/Downloads/super-productivity-backup.json --collection_projects Aktive__Projekte,Geparkte__Projekte
```

Import the created file `super_productivity_updated_backup_file.json` into Super Productivty.
