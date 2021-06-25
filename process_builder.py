import jsonpickle
import urllib.parse

contact_pb_dict = {
    'AS_Premium_News_Content': 3,
    'Auto_Populate_Opportunity_Field_in_Contact_Record': 9,
    'Auto_Populate_Renewal_Opportunity_Field_in_Contact_Record': 4,
    'Corp_Investor_Relations_PositionId_Update': 2,
    'MCO_Financial_Inst_Global_AS_TRUE': 2,
    'MCO_Fundamental_Global_AS_TRUE': 2,
    'Set_up_trial_config': 9,
    'Turn_on_Moody_s_Credit_Research_Capital_Markets': 2,
    'Turn_on_underlying_MCO_Corporate_Global_AS_fields': 2
}

opp_pb_dict = {
    'Assign_primary_contact': 3,
    'Opp_Stage_Date_Stamps': 3,
    'Update_Opportunity_Intacct_Entity': 1,
    'Deal_Source': 6,
    'Opportunity_Account_Manager_for_Won_Upsell_Opps': 4

}


def get_all_pb_processes(sfdc_client):
    query = 'Select Id,ActiveVersion.VersionNumber,LatestVersion.VersionNumber,DeveloperName From FlowDefinition'

    cleaned_query = urllib.parse.quote_plus(query)
    response = sfdc_client.restful(path=f'tooling/query/?q={cleaned_query}')


    return {pb['Id']: pb for pb in response['records']}


def toggle_pb_process(sfdc_client, process_id, version_num=None):
    pb = {
        'Metadata': {
            'activeVersionNumber': version_num
        }
    }

    pb_str = jsonpickle.encode(pb, unpicklable=False)
    response = None

    try:
        # The response coming from Salesforce is apparently malformed and fails to parse properly
        response = sfdc_client.restful(path=f'tooling/sobjects/FlowDefinition/{process_id}/', method='PATCH', data=pb_str)
    except Exception as ex:
        if 'Expecting value' not in str(ex):
            print(ex)


def toggle_processes(sfdc_client, activate: bool=False, sobject: str='Contact'):
    pb_map = get_all_pb_processes(sfdc_client)

    for pb_id, pb in pb_map.items():
        pb_id = pb['Id']
        pb_name = pb['DeveloperName']


        working_dict = contact_pb_dict

        if sobject == 'Opportunity':
            working_dict = opp_pb_dict

        if pb_name in working_dict.keys():
            active_version = None

            if activate:
                active_version = working_dict[pb_name]

            print(f'{"Activating" if activate else "Deactivating"} process {pb_name}')
            toggle_pb_process(sfdc_client, pb_id, active_version)