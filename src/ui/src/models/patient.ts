export interface Patient {
  patient_id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  birth_date: Date;
  address: {
    line: string;
    city: string;
    state: string;
    postal_code: string;
  };
}
