# Record Linker Postman Collection Guide

## Set up
To use the Record Linker Postman collection, you must:
1. install [Docker](https://docs.docker.com/get-docker/)
2. run Record Linker API locally on port 8000 (see below for details)
3. set up [Postman](https://www.postman.com/downloads/) or any similar API testing tool to send and inspect HTTP requests
4. Import the Record Linker Postman Collection. See directions for importing and running collections [here](https://learning.postman.com/docs/collections/running-collections/working-with-data-files/).

### Record Linker API Local Set Up
There are two ways to get the Record Linker API set up locally:
1. Run `docker run -v ./:/tmp -e DB_URI=sqlite:////tmp/db.sqlite3 -e PORT=8000 -p 8000:8000 ghcr.io/cdcgov/recordlinker:latest`
2. Clone the Record Linker repo and run the API using `local_server.sh`. See the `Getting Started` section [here](https://github.com/CDCgov/RecordLinker?tab=readme-ov-file#getting-started).


## Record Linker Postman Collection Examples
The Record Linker Postman Collection includes the following examples to demonstrate some of Record Linker's API functionality: 

1. **Reset MPI**: deletes all data from the MPI 
2. **Seed MPI**: adds a handful of records to the MPI
3. **Get Algorithm**: retrieves all of the algorithm configurations stored in the database; currently just shows the DIBBs default algorithm. 
4. **Add new Patient (A1)**: adds a new patient with `external_id` set to `A1`. This patient does not match any of the existing records in the MPI. A new `person_id` is created for this patient.
5. **Add Patient (A1) with no address or MRN**: adds another instance of Patient A1, but this time the incoming record does not contain the patient's address or MRN, potentially representing data from an ELR. This new record matches to Patient A1 and is assigned the same `person_id`, linking the two records together.
6. **Add Patient (A1) with no address, MRN, or DOB**: adds another instance of Patient A1, but this time the incoming record does not contain the patient's address, MRN, or birthdate. There is too much missing information from this incoming record to confidently match it to any existing record so it is assigned a new `person_id`. 
7. **Add Patient (A1)'s father (A2)**: adds a new patient record representing Patient A1's father. The incoming record has the same name as Patient A1 (except A2 has the "Sr." suffix), same address, and same MRN (representing a potential data entry mistake at a hospital). The incoming record has a different birthdate. The incoming record does not match any existing records so it is assigned a new `person_id`. 
8. **Add new Patient (B1) with same address as A1**: adds a new record who lives at the same address as Patient A1 but otherwise has different information, representing a congregate living facility such as an apartment or nursing home. The incoming record does not match any existing record so it is assigned a new `person_id`. 


To see the full API documentation for all of Record Linker's capabilities, go to http://localhost:8000/api/redoc after spinning up the Record Linker API locally. 

