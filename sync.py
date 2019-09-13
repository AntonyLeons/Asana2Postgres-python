import os
import sys

import psycopg2
from asana import *

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

customfields = []


# Instructions
#
# 1. Set your ASANA_ACCESS_TOKEN environment variable to a Personal Access Token obtained in your Asana Account Settings
#
# This simple script asks the user to choose from their available Workspaces and then the first page (if more than a
# single page exists) of available projects in order to create a task in that project.
#
def getCustom(a):
    if "enum" == a["resource_subtype"] and a["enum_value"] is not None:
        return a["enum_value"]["name"]
    elif "text" == a["resource_subtype"] and a["text_value"] is not None:
        return a["text_value"]
    elif "number" == a["resource_subtype"] and a["number_value"] is not None:
        return a["number_value"]
    else:
        return ""


try:
    table = "tickets"
    project_id = 1139602359227529
    if len(sys.argv) == 2:
        project_id = sys.argv[1].strip()
        table = "asana.T" + project_id
    elif len(sys.argv) == 3:
        project_id = sys.argv[1].strip()
        table = "asana." + sys.argv[2].strip()
    connection = psycopg2.connect(user=os.environ['MB_DB_USER'],
                                  password=os.environ['MB_DB_PASS'],
                                  host=os.environ['MB_DB_HOST'],
                                  port=os.environ['MB_DB_PORT'],
                                  database=os.environ['MB_DB_DBNAME'])
    cursor = connection.cursor()
    offset = None
    GetModified = 'SELECT MAX("Modified") FROM '+table
    cursor.execute(GetModified)
    result = cursor.fetchall()
    for row in result:
        maximum = row[0]
    if 'ASANA_ACCESS_TOKEN' in os.environ:
        client = Client.access_token(os.environ['ASANA_TOKEN'])
        client.options['page_size'] = 100
        client.headers = {"Asana-Enable": "string_ids"}
        counter = 0
        while True:
            client.options['offset'] = offset
            customdic = {}
            tasks = client.tasks.search_in_workspace(2740660799089,
                                                     {"project.any": project_id,
                                                      "modified_on.after": maximum.date(),
                                                      "opt_fields": "gid, created_at, due_on, completed_at, completed, "
                                                                    "modified_at, name, notes, assignee, assignee.name, "
                                                                    "assignee.email, tags, custom_fields, "
                                                                    "custom_fields.enum_value, "
                                                                    "custom_fields.resource_subtype,"
                                                                    " custom_fields.text_value, "
                                                                    "custom_fields.number_value, custom_fields.name"})
            for task in tasks:
                created_at = task["created_at"]
                completed_at = task["completed_at"]
                modified_at = task["modified_at"]
                name = task["name"] if task["name"] is not None else ''
                notes = task["notes"] if task["notes"] is not None else ''
                due_on = task["due_on"]
                assignee_name = ""
                assignee_email = ""

                if task["assignee"] is not None:
                    assignee_name = task["assignee"]["name"] if task["assignee"]["name"] is not None else ''
                    assignee_email = task["assignee"]["email"] if task["assignee"]["email"] is not None else ''

                for customf in task["custom_fields"]:
                    customdic[customf["name"].replace(" ", "_")] = getCustom(customf)

                tags = task["tags"] if task["tags"] is not None else ''

                SQL = '''INSERT INTO ''' + table + ''' ("ID", "Created_Date", "Completed_At", "Completed", "Modified", "Name", 
                "Assignee", "Assignee_Email", "Due_On", "Tags", "Notes") VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s) ON CONFLICT ("ID") DO UPDATE SET "Created_Date" = excluded."Created_Date", 
                "Completed_At" = excluded."Completed_At", "Completed" = excluded."Completed", 
                "Modified"=excluded."Modified", "Name"=excluded."Name", "Assignee"=excluded."Assignee", 
                "Assignee_Email"=excluded."Assignee_Email", "Due_On"=excluded."Due_On",
                "Tags"=excluded."Tags", "Notes"=excluded."Notes"; '''
                data = (task["gid"], created_at, completed_at, task["completed"],
                        modified_at, name, assignee_name, assignee_email,
                        due_on,
                        tags, notes)
                cursor.execute(SQL, data)
                connection.commit()
                for key, value in customdic.items():
                    if key in customfields:
                        sql2 = 'UPDATE ' + table + ' SET "' + key + '" = %s WHERE "ID" =%s'
                        var = (value, task["gid"])
                        cursor.execute(sql2, var)
                        connection.commit()
                counter += 1

            if 'next_page' in tasks:
                print("Next Page")
                offset = tasks['next_page']['offset']
            else:
                print(f"{counter} tasks modified")
                break
    else:
        print("ACCESS TOKEN MISSING")

finally:
    print("PostgreSQL connection is closed")
