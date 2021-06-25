# Import Format:
# 1. Standard Library full import
# 2. External Library full import
# 3. Standard Library from import
# 4. External Library from import
# 5. User package full import
# 6. User package from import
#
import logging

from simple_salesforce import Salesforce
from apscheduler.schedulers.blocking import BlockingScheduler

import config
import process_builder as pb
import package_logger

# logging.basicConfig()
package_logger.initialize_logging()

def run_script():

    exit_flag = True
    while exit_flag:
        opp_id = input('Please provide Opportunity Id: \n\n')

        if opp_id == 'q':
            exit(0)
        elif not opp_id.startswith('006'):
            logging.error('This is not an Opportunity Id, why you so stupid, stupid?')
        else:
            success = execute_sfdc_update(opportunity_id=opp_id)

            if success:
                exit(0)


def execute_sfdc_update(opportunity_id: str):
    uname = config.SalesforceConfig['username']
    pwd = config.SalesforceConfig['password']
    sec_t = config.SalesforceConfig['security_token']

    # For Production Salesforce, login domain lives at https://login.salesforce.com
    # There, we pass 'login' as the value for the param domain
    # sfdc_client = Salesforce(username=uname, password=pwd, security_token=sec_t, domain='login')

    # For Sandbox, you need to change domain to test
    # URL for sandbox login is https://test.salesforce.com
    # sfdc_sandbox_client = Salesforce(username=uname, password=pwd, security_token=sec_t, domain='test')

    # f-string
    # my_string = f"blah blah blah {opportunity_id}"
    # my_string_2 = "blah blah blah" + opportunity_id

    # Step 0. Login to Salesforce, establish a "client" to be used for all SFDC work
    sfdc_client = Salesforce(username=uname, password=pwd, security_token=sec_t, domain='login')

    # Step 1. Turn off PBs
    pb.toggle_processes(sfdc_client=sfdc_client, activate=False, sobject='Contact')

    # Step 2. Query for Account Manager Id from Opportunity Account
    soql_opp = f"SELECT Id, AccountId, Account.Account_Manager_2__c, IsWon FROM Opportunity WHERE Id = '{opportunity_id}' LIMIT 1"
    opps = sfdc_client.query_all(soql_opp)['records']

    if not opps:
        logging.error(f'Failed to retrieve Opportunity with Id {opportunity_id}. Please enter a new Id.')
        return False

    o = opps[0]
    account_id = o['AccountId']
    account_manager_id = o['Account']['Account_Manager_2__c']
    is_won = o['IsWon']

    if not is_won:
        logging.debug('This Opportunity is not marked Closed-Won, cannot continue.')
        return False

    # Step 3. Query for all Contacts associated with the Opp
    soql_contacts = f"SELECT Id, OwnerId FROM Contact WHERE AccountId = '{account_id}'"
    resp = sfdc_client.query_all(soql_contacts)
    contacts = resp['records']

    # Step 4. Loop through all Contacts, if Contact Owner != Account AM, update Contact owner
    # For bulk updates, we need to setup a list of payloads
    contacts_for_update = []
    for cnt in contacts:
        cnt_id = cnt['Id']
        owner_id = cnt['OwnerId']

        if owner_id != account_manager_id:
            c = contact_payload(contact_id=cnt_id, account_manager_id=account_manager_id)

            contacts_for_update.append(c)

    # Step 5. Push Updates to Salesforce

    sfdc_client.bulk.Contact.update(contacts_for_update)

    # Step 6. Turn on PBs.
    pb.toggle_processes(sfdc_client=sfdc_client, activate=True, sobject='Contact')

    logging.info('Done!')
    return True


def contact_payload(contact_id: str, account_manager_id: str):
    c = {
        "Id": contact_id,
        "OwnerId": account_manager_id
    }

    return c

def execute_scheduled_update():
    uname = config.SalesforceConfig['username']
    pwd = config.SalesforceConfig['password']
    sec_t = config.SalesforceConfig['security_token']
    # Step 0. Login to Salesforce, establish a "client" to be used for all SFDC work
    sfdc_client = Salesforce(username=uname, password=pwd, security_token=sec_t, domain='login')

    try:

        logging.info("Currently disabling process...")
        # Step 1. Turn off PBs
        pb.toggle_processes(sfdc_client=sfdc_client, activate=False, sobject='Contact')

        # Step 2. Query for Account Manager Id from Opportunity Account
        opp_soql_query = f"SELECT Id, AccountId, Account.Account_Manager_2__c, IsWon FROM Opportunity WHERE IsWon = true AND CloseDate >= YESTERDAY"
        logging.info("Querying Salesforce for Opportunities...")
        opp_resp = sfdc_client.query_all(opp_soql_query)

        # if varible = '', 0, [], {}, set(), None
        if opp_resp:
            opp_records = opp_resp['records']
        else:
            raise Exception('No Opps return from query.')

        # Loop through all the opps and get the account_id for each one

        # account_manager_id = opp['Account']['Account_Manager_2__c']
        # is_won = opp['IsWon']
        account_ids = set()
        account_manager_map = {}
        for opp in opp_records:
            account_id = opp['AccountId']
            account_ids.add(account_id)

            account_manager_map[account_id] = opp['Account']['Account_Manager_2__c']

        # SFDC requires soql IN queries to have ids in single quotes seperated by a comma

        acct_ids_for_query = [f"'{id}'" for id in account_ids]
        acct_ids_str = ','.join(acct_ids_for_query)

        soql_contacts = f"SELECT Id, AccountId, OwnerId FROM CONTACT WHERE AccountId IN ({acct_ids_str})"
        logging.info("Querying Salesforce for Contacts...")
        contact_resp = sfdc_client.query_all(soql_contacts)

        if contact_resp:
            contacts = contact_resp['records']
        else:
            raise Exception(f"Error: No contacts were found")

        contacts_for_update = []
        for cnt in contacts:
            cid = cnt['Id']
            account_id = cnt['AccountId']
            owner_id = cnt['OwnerId']
            acct_manager_id = account_manager_map[account_id]

            if owner_id != acct_manager_id:
                payload = contact_payload(contact_id=cid, account_manager_id=acct_manager_id)
                contacts_for_update.append(payload)

        logging.info("Updating Salesforce...")
        sfdc_client.bulk.Contact.update(contacts_for_update)

        logging.info("Turning processes back on...")
        # Step 6. Turn on PBs.
        pb.toggle_processes(sfdc_client=sfdc_client, activate=True, sobject='Contact')

        logging.info('Done!')

    except Exception as ex:
        logging.error('An error occurred trying to update contacts. See exception')
        logging.exception(ex)



def schedule_run():

    # instantiate the Scheduler Class
    # Blocking Scheduler will pause any running processes until the scheduled process completes
    scheduler = BlockingScheduler()
    # hour=1 == 7pm EST b/c Heroku runs on GMT
    scheduler.add_job(execute_scheduled_update, 'cron', hour=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit) as ex:
        logging.exception(ex)



if __name__ == '__main__':
    logging.info("Logging has initialized")
    print("Logging test!")
    schedule_run()
    # execute_scheduled_update()