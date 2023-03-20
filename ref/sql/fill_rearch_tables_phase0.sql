-- FILL NEW ADDRESSES TABLES --

-- Current names: lookup table is application_addressesnew_rearch, user table is application_addresses_rearch
-- Place the same ID as the mailing and eligibility addresses for this initial fill
-- Field mapping is as such (application_addresses, application_addressesnew_rearch, application_addresses_rearch):
--     created, created_at, created_at
--     modified, modified_at, modified_at
--     user_id_id, NULL, user_id
--     address, address1, NULL
--     address2, address2, NULL
--     city, city, NULL
--     state, state, NULL
--     zipCode, zip_code, NULL
--     isInGMA, is_in_gma, NULL
--     isInGMA, is_city_covered, NULL
--     hasConnexion, has_connexion, NULL
--     is_verified, is_verified, NULL
--     NULL, id (auto-incremented), eligibility_address_id
--     NULL, id (auto-incremented), mailing_address_id

--When necessary: truncate addresses_new_rearch
--truncate table public.application_addressesnew_rearch cascade;

-- Insert into the rearchitected lookup table
-- Ensure all parts of the input addresses are uppercase (to match the .clean() function in the model)
insert into public.application_addressesnew_rearch ("created_at", "modified_at", "address1", "address2", "city", "state", "zip_code", "is_in_gma", "is_city_covered", "has_connexion", "is_verified")
	select "created", "modified", UPPER("address"), UPPER("address2"), UPPER("city"), UPPER("state"), "zipCode", "isInGMA", "isInGMA", "hasConnexion", "is_verified"
	from public.application_addresses
	order by "created" asc
	on conflict do nothing;

-- Gather user ID and lookup table ID to insert into addresses_rearch
insert into public.application_addresses_rearch ("created_at", "modified_at", "user_id", "eligibility_address_id", "mailing_address_id")
	select r."created_at", r."modified_at", o."user_id_id", r."id", r."id" from public.application_addressesnew_rearch r
		right join public.application_addresses o on 
		upper(o."address")=r."address1" and
		upper(o."address2")=r."address2" and
		upper(o."city")=r."city" and
		upper(o."state")=r."state" and
		o."zipCode"=r."zip_code";
	
-- FILL NEW AMI TABLE --

-- Current name: AMI table is application_ami_rearch
-- Field mapping is as such (application_ami, application_ami_rearch):
--     created, created_at
--     modified, modified_at
--     2022, year_valid
--     householdNum, number_persons_in_household
--     True, is_active
--     ami, ami

insert into public.application_ami_rearch ("created_at", "modified_at", "year_valid", "number_persons_in_household", "is_active", "ami")
	select "created", "modified", 2022, "householdNum", True, "ami" 
	from public.application_ami;

-- Insert prior year's AMI values (that had to be replaced because the application_ami table's keys wouldn't allow them)
insert into public.application_ami_rearch ("created_at", "modified_at", "year_valid", "is_active", "number_persons_in_household", "ami")
	values
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '1', 65900),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '2', 75300),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '3', 84700),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '4', 94100),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '5', 101700),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '6', 109200),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '7', 116700),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, '8', 124300),
		('2021-09-29 16:10:37', '2021-09-29 16:10:37', 2021, False, 'Each Additional', 4480)
		;

-- FILL NEW ELIGIBILITY TABLE --

-- Current name: eligibility table is application_eligibility_rearch
-- Field mapping is as such (application_eligibility, application_eligibility_rearch):
--     created, created_at
--     modified, modified_at
--     user_id_id, user_id
--     rent, duration_at_address
--     dependents, number_persons_in_household
--     <2021 or 2022>, depending on created date, ami_year
--     AmiRange_min, ami_range_min
--     AmiRange_max, ami_range_max
--     True if GenericQualified='ACTIVE' else False, is_income_verified

-- 2022 AMI values were updated 2022-08-08 02:31 UTC, so ami_year=2021 before and including then
insert into public.application_eligibility_rearch ("created_at", "modified_at", "user_id", "duration_at_address", "number_persons_in_household", "ami_year", "ami_range_min", "ami_range_max", "is_income_verified")
	select "created", "modified", "user_id_id", "rent", "dependents", 2021, "AmiRange_min", "AmiRange_max", (case when "GenericQualified"='ACTIVE' then true else false end)
	from public.application_eligibility
	where "created"<='2022-08-08 02:31:00';

-- ami_year=2022 after the update date
insert into public.application_eligibility_rearch ("created_at", "modified_at", "user_id", "duration_at_address", "number_persons_in_household", "ami_year", "ami_range_min", "ami_range_max", "is_income_verified")
	select "created", "modified", "user_id_id", "rent", "dependents", 2022, "AmiRange_min", "AmiRange_max", (case when "GenericQualified"='ACTIVE' then true else false end)
	from public.application_eligibility
	where "created">'2022-08-08 02:31:00';

-- FILL NEW MOREINFO TABLE --

-- Current name: application_moreinfo_rearch
-- Field mapping is as such (application_moreinfo, application_moreinfo_rearch):
--     created, created_at
--     modified, modified_at
--     user_id_id, user_id
--     dependentInformation, household_info

-- Due to intensive conversions, the majority of this section needs to be run via Django. Switch to branch database-rearchitecture-p0-modifytable, then run getfoco via VSCode against the preferred target database and navigate to 127.0.0.1:8000/application/rearch_phase0 to write the initial table --

-- modified_at is written automatically, so now we need to overwrite it from the temporary fields
update public.application_moreinfo_rearch set "created_at"="created_at_init_temp", "modified_at"="modified_at_init_temp";

select "init_temp VARS CAN NOW BE DELETED VIA DJANGO MODELS" from public.application_moreinfo_rearch;

-- FILL IQ PROGRAMS TABLES --

-- Current name: application_iqprogramqualifications_rearch
-- Field mapping is as such (application_iqprogramqualifications, application_iqprogramqualifications_rearch):
--     created, created_at
--     modified, modified_at
--     name, program_name
--     percentAmi, ami_threshold
--     Fill additional fields with empty strings to fullfil non-null contraints

insert into public.application_iqprogramqualifications_rearch ("created_at", "modified_at", "program_name", "ami_threshold", "friendly_name", "friendly_category", "friendly_description", "friendly_supplemental_info", "learn_more_link", "friendly_eligibility_review_period")
	select "created", "modified", "name", "percentAmi", '', '', '', '', '', ''
	from public.application_iqprogramqualifications;

-- Also add the defunct SPIN Community Pass
insert into public.application_iqprogramqualifications_rearch ("created_at", "modified_at", "program_name", "ami_threshold", "friendly_name", "friendly_category", "friendly_description", "friendly_supplemental_info", "learn_more_link", "friendly_eligibility_review_period", "is_active") values
	('2022-07-20 18:48:00.000', '2022-07-20 18:48:00.000', 'spin_community_pass', 0.3, '', '', '', '', '', '', False);

-- Current name: application_iq_programs_rearch
-- Field mapping is as such (application_eligibility, application_iq_programs_rearch):
--     created, applied_at
--     '1970-01-01 00:00:00', enrolled_at (this will need to be updated via Python based on the historical income verification returned extracts)
--     user_id_id, user_id
--     for the rest, there isn't so much a field mapping as a loose connectivity that I'll recreate through this query

-- Also need the ID from application_iqprogramqualifications_rearch
-- Run for Connexion
insert into application_iq_programs_rearch ("applied_at", "enrolled_at", "user_id", "is_enrolled", "program_id")
	select "created", '1970-01-01 00:00:00', "user_id_id", (case when "ConnexionQualified"='ACTIVE' then true else false end), (select id from public.application_iqprogramqualifications_rearch where program_name='connexion')
	from public.application_eligibility
	where "ConnexionQualified"='ACTIVE' or "ConnexionQualified"='PENDING';

-- Run for Grocery Rebate
insert into application_iq_programs_rearch ("applied_at", "enrolled_at", "user_id", "is_enrolled", "program_id")
	select "created", '1970-01-01 00:00:00', "user_id_id", (case when "GRqualified"='ACTIVE' then true else false end), (select id from public.application_iqprogramqualifications_rearch where program_name='grocery')
	from public.application_eligibility
	where "GRqualified"='ACTIVE' or "GRqualified"='PENDING';

-- Run for Recreation
insert into application_iq_programs_rearch ("applied_at", "enrolled_at", "user_id", "is_enrolled", "program_id")
	select "created", '1970-01-01 00:00:00', "user_id_id", (case when "RecreationQualified"='ACTIVE' then true else false end), (select id from public.application_iqprogramqualifications_rearch where program_name='recreation')
	from public.application_eligibility
	where "RecreationQualified"='ACTIVE' or "RecreationQualified"='PENDING';

-- Run for SPIN
insert into application_iq_programs_rearch ("applied_at", "enrolled_at", "user_id", "is_enrolled", "program_id")
	select "created", '1970-01-01 00:00:00', "user_id_id", (case when "SPINQualified"='ACTIVE' then true else false end), (select id from public.application_iqprogramqualifications_rearch where program_name='spin')
	from public.application_eligibility
	where "SPINQualified"='ACTIVE' or "SPINQualified"='PENDING';

-- Run for defunct SPIN Community Pass
insert into application_iq_programs_rearch ("applied_at", "enrolled_at", "user_id", "is_enrolled", "program_id")
	select "created", '1970-01-01 00:00:00', "user_id_id", (case when "SpinAccessQualified_depr"='ACTIVE' then true else false end), (select id from public.application_iqprogramqualifications_rearch where program_name='spin_community_pass')
	from public.application_eligibility
	where "SpinAccessQualified_depr"='ACTIVE' or "SpinAccessQualified_depr"='PENDING';

-- FILL ELIGIBILITY PROGRAMS TABLES --

-- Current name: application_programs_rearch
-- There is no field mapping for this; everything until now has been hardcoded in Python

insert into public.application_programs_rearch ("created_at", "modified_at", "program_name", "ami_threshold", "friendly_program_name", "is_active") values
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'snap', 0.3, 'Supplemental Nutrition Assistance Program (SNAP)', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'medicaid', 0.3, 'Medicaid', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'free_reduced_lunch', 1.5, 'Poudre School District Free and Reduced Lunch', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'identification', 1, 'Identification Card', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'ebb_acf', 1.5, 'Affordable Connectivity Program (ACP)', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', 'leap', 1.5, 'Low-income Energy Assistance Program (LEAP)', True),
	('2023-03-19 18:00:00', '2023-03-19 18:00:00', '1040', 1, '1040 Tax Form', False)
	;

-- Current name: application_dashboard_form_rearch
-- Field mapping is as such (dashboard_form, application_dashboard_form_rearch):
--     created, created_at
--     modified, modified_at
--     user_id_id, user_id
--     document, document_path
--     There's no direct mapping from dashboard_form to get the program_id, so I'm going to do it manually based on the unique document_title values *from PROD*

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='snap')
	from public.dashboard_form
	where document_title='SNAP';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='medicaid')
	from public.dashboard_form
	where document_title='Medicaid';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='free_reduced_lunch')
	from public.dashboard_form
	where document_title='Free and Reduced Lunch';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='identification')
	from public.dashboard_form
	where document_title='Identification';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='ebb_acf')
	from public.dashboard_form
	where document_title='ACP Letter';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='leap')
	from public.dashboard_form
	where document_title='LEAP Letter';

insert into public.application_dashboard_form_rearch ("created_at", "modified_at", "user_id", "document_path", "program_id")
	select "created", "modified", "user_id_id", "document", (select id from public.application_programs_rearch where program_name='1040')
	from public.dashboard_form
	where document_title='1040' or document_title='1040 Form';