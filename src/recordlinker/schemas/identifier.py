import enum
import re
import typing

import pydantic


class IdentifierType(enum.Enum):
    """
    Enum for various identifier types.
    """
    AC = "AC"
    ACSN = "ACSN"
    AIN = "AIN"
    AM = "AM"
    AMA = "AMA"
    AN = "AN"
    ANC = "ANC"
    AND = "AND"
    ANON = "ANON"
    ANT = "ANT"
    APRN = "APRN"
    ASID = "ASID"
    BA = "BA"
    BC = "BC"
    BCFN = "BCFN"
    BCT = "BCT"
    BR = "BR"
    BRN = "BRN"
    BSNR = "BSNR"
    CAII = "CAII"
    CC = "CC"
    CONM = "CONM"
    CY = "CY"
    CZ = "CZ"
    DC = "DC"
    DCFN = "DCFN"
    DDS = "DDS"
    DEA = "DEA"
    DFN = "DFN"
    DI = "DI"
    DL = "DL"
    DN = "DN"
    DO = "DO"
    DP = "DP"
    DPM = "DPM"
    DR = "DR"
    DS = "DS"
    DSG = "DSG"
    EI = "EI"
    EN = "EN"
    ESN = "ESN"
    FDR = "FDR"
    FDRFN = "FDRFN"
    FGN = "FGN"
    FI = "FI"
    FILL = "FILL"
    GI = "GI"
    GIN = "GIN"
    GL = "GL"
    GN = "GN"
    HC = "HC"
    IND = "IND"
    IRISTEM = "IRISTEM"
    JHN = "JHN"
    LACSN = "LACSN"
    LANR = "LANR"
    LI = "LI"
    LN = "LN"
    LR = "LR"
    MA = "MA"
    MB = "MB"
    MC = "MC"
    MCD = "MCD"
    MCN = "MCN"
    MCR = "MCR"
    MCT = "MCT"
    MD = "MD"
    MI = "MI"
    MR = "MR"
    MRT = "MRT"
    MS = "MS"
    NBSNR = "NBSNR"
    NCT = "NCT"
    NE = "NE"
    NH = "NH"
    NI = "NI"
    NII = "NII"
    NIIP = "NIIP"
    NP = "NP"
    NPI = "NPI"
    OBI = "OBI"
    OD = "OD"
    PA = "PA"
    PC = "PC"
    PCN = "PCN"
    PE = "PE"
    PEN = "PEN"
    PGN = "PGN"
    PHC = "PHC"
    PHE = "PHE"
    PHO = "PHO"
    PI = "PI"
    PIN = "PIN"
    PLAC = "PLAC"
    PN = "PN"
    PNT = "PNT"
    PPIN = "PPIN"
    PPN = "PPN"
    PRC = "PRC"
    PRN = "PRN"
    PT = "PT"
    QA = "QA"
    RI = "RI"
    RN = "RN"
    RPH = "RPH"
    RR = "RR"
    RRI = "RRI"
    RRP = "RRP"
    SAMN = "SAMN"
    SB = "SB"
    SID = "SID"
    SL = "SL"
    SN = "SN"
    SNBSN = "SNBSN"
    SNO = "SNO"
    SP = "SP"
    SR = "SR"
    SRX = "SRX"
    SS = "SS"
    STN = "STN"
    TAX = "TAX"
    TN = "TN"
    TPR = "TPR"
    TRL = "TRL"
    U = "U"
    UDI = "UDI"
    UPIN = "UPIN"
    USID = "USID"
    VN = "VN"
    VP = "VP"
    VS = "VS"
    WC = "WC"
    WCN = "WCN"
    WP = "WP"
    XV = "XV"
    XX = "XX"

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Identifier(pydantic.BaseModel):
    """
    The schema for an Identifier record
    """

    model_config = pydantic.ConfigDict(extra="allow")

    type: IdentifierType
    value: str
    authority: typing.Optional[str] = None

    @classmethod
    def model_construct(
        cls, _fields_set: set[str] | None = None, **values: typing.Any
    ) -> typing.Self:
        """
        Construct a new instance of the Identifier model
        """
        values["type"] = IdentifierType(values["type"])
        return super().model_construct(_fields_set=_fields_set, **values)

    @pydantic.field_validator("type", mode="before")
    def parse_type(cls, value):
        """
        Parse type string into an IdentifierType enum
        """
        if value: 
            return IdentifierType(value)
        return value

    @pydantic.field_validator("value", mode="before")
    def parse_value(cls, value: str, info: pydantic.ValidationInfo):
        """
        Parse the value string
        """
        # NOTE: Define "type" before "value" in the field definitions to guarentee that it will be available here.
        identifier_type = info.data["type"]
        if identifier_type == IdentifierType.SS:       
            val = str(value).strip()

            if re.match(r"^\d{3}-\d{2}-\d{4}$", val):
                return val

            if len(val) != 9 or not val.isdigit():
                return ''

            # Format back to the standard SSN format (XXX-XX-XXXX)
            formatted_ssn = f"{val[:3]}-{val[3:5]}-{val[5:]}"
            return formatted_ssn
        
        return value