# Reference

## Algorithm Configuration

The Algorithm configurations are stored in the database and can be managed via the API.
Many of the attributes defined on a configuration are limited to a specific set of values,
which are defined here.

### Blocking Key Types

The `BlockingKey` enum defines the types of blocking values that are generated from the 
patient data and used during query retrieval. The following blocking key types are supported:

`BIRTHDATE` (ID: **1**)

:   The patients birthdate in the format `YYYY-MM-DD`.

`MRN` (ID: **2**)

:   The last 4 characters of a patient's medical record number.

`SEX` (ID: **3**)

:   The patient's sex in the format of `M`, `F`, or `U` for unknown.

`ZIP` (ID: **4**)

:   The patient's  5 digit zip code.

`FIRST_NAME` (ID: **5**)

:   The first 4 characters of the patient's first name.

`LAST_NAME` (ID: **6**)

:   The first 4 characters of the patient's last name.

`ADDRESS` (ID: **7**)

:   The first 4 characters of the patient's address.
