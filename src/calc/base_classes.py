import math
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any


@dataclass
class BaseGeometry:
    name: str
    ElementID: str
    d: float
    t: float
    Fabrication: str
    cs_type : str = field(default=None)



    steel_grade: float = field(default=None)
    steel_grade_str: str = field(default=None)
    css_class: int = field(default=None)

    A_provided: float = field(default=None, repr=False)
    Iy_provided: float = field(default=None, repr=False)
    Iz_provided: float = field(default=None, repr=False)

    Iz: float = field(default=None, repr=False)

    W_el_y_provided: float = field(default=None, repr=False)
    W_el_z_provided: float = field(default=None, repr=False)

    W_el_z: float = field(default=None, repr=False)

    W_pl_y_provided: float = field(default=None, repr=False)
    W_pl_z_provided: float = field(default=None, repr=False)

    W_pl_z: float = field(default=None, repr=False)

    It: float = field(default=None, repr=False)
    Avy: float = field(default=None, repr=False)
    Avz: float = field(default=None, repr=False)


    @property
    def A(self) -> float:
        """Calculate the cross-sectional area of the tube in [m2].
        Or if it prov in csv_cross_section csv its not going to be calculated
        """
        if self.A_provided is not None:
            return self.A_provided
        tube_area = (math.pi * (self.d ** 2 - (self.d - (2 * self.t)) ** 2)) / 4
        return tube_area
    @property
    def I(self) -> float:
        """Calculate the cross-sectional moment of inertia tube in [m4]."""
        if self.Iy_provided is not None:
            return self.Iy_provided
        D = self.d
        d = (self.d - 2 * self.t)
        I = math.pi * (D ** 4 - d ** 4) / 64
        return I
    @property
    def W_el(self) -> float:
        """ Calculate elastic cross-sectional module in [m3]"""
        if self.W_el_y_provided is not None:
            return self.W_el_y_provided

        W_el = self.I / (self.d/2)

        return W_el
    @property
    def W_pl(self) -> float:

        if self.W_pl_y_provided is not None:
            return self.W_pl_y_provided
        t = self.t
        d = self.d
        W_pl = t**3 * ((d/t)-1)**2

        return W_pl

    @property
    def N_max(self) -> float:
        """Max Tension resistance of the tube"""
        N_max = self.A * self.steel_grade
        return N_max
    @property
    def M_max_el(self) -> float:
        """Max elastic bending resistance"""
        M_max = self.W_el * self.steel_grade
        return M_max
    @property
    def M_max_pl(self) -> float:

        M_max_pl = self.W_pl * self.steel_grade

        return M_max_pl

    def get_base(self, attribute_name: str, default=None):
        """Get the value of the attribute if it exists, otherwise return default."""
        return getattr(self, attribute_name, default)


@dataclass
class RectangleHollow(BaseGeometry):
    b: float = field(default=float(0))
    h: float = field(default=float(0))


@dataclass
class ConfigConn:
    profiles_chord:str
    profiles_conn_m:str
    validity_conditions:list[str]
    idea_conn_path:str
    equations:dict
    add_exlus_conds: Optional[dict] = None


@dataclass
class ConnSetup:
    conn_type: str
    code_standard: str
    config_:ConfigConn
    nrd_direction:str
    c_angle: float = None
    steel_grade:float = None
    steel_grade_str:str = None
    chord: Union[BaseGeometry, RectangleHollow] = None
    conn_member: Union[BaseGeometry, RectangleHollow] = None
    exclude_reason: str = None


    def get_conn(self, attribute_name: str, default=None):
        """Get the value of the attribute if it exists, otherwise return default."""
        return getattr(self, attribute_name, default)


@dataclass
class CodeRes:
    Nrd: float
    kp_my_sql_key: float
    res_dict: Dict[str, Any] = field(default_factory=dict)
    #recalculated results
    Nrd_recalc:float = None
    kp_my_sql_key_recalc:float = None
    res_dict_recalc: Optional[Dict[str, Any]] = None
    #thing for sharing
    n_chord_new:float = None
    m_chord_new: float = None


@dataclass
class IdeaLoad:
    n:float = None
    vy: float = None
    vz: float = None
    my: float = None
    mz: float = None
    mx: float = None
    position:str = None


@dataclass
class IdeaLoadingInfo:
    force_scale_factor:float
    vertical_reaction:float
    force:str
    beam_name_idea:str
    position:str
    chord_begin: IdeaLoad = None
    chord_end: IdeaLoad = None
    conn_member_end: IdeaLoad = None
    conn_member_2_end: IdeaLoad = None


@dataclass
class IdeaRes:
    """
    Attributes:
        fy:float: fy of the most utilized plastic strain plate
        division_of_the_chs: actual division which is set in the model

    """
    Nrd_idea:float
    analysis_perc:float
    fy:float
    division_of_the_chs:float
    weld_parts:int
    min_weld_parts:int
    chord_strain:float = None
    conn_member_strain:float = None


@dataclass
class MainCalculationInfo:
    conn_setup:ConnSetup
    perc_chord_N: float
    perc_chord_M: float

    my_sql_key:str = None
    results: CodeRes = None
    idea_results:IdeaRes = None
    idea_loading: IdeaLoadingInfo = None

    @property
    def N_chord(self) -> float :

        N_max = self.conn_setup.chord.N_max

        N_chord = (N_max * self.perc_chord_N)

        return N_chord


    @property
    def M_chord(self) -> float:

        M_max = self.conn_setup.chord.M_max_el

        M_chord = M_max * self.perc_chord_M

        return M_chord


    @property
    def end_length_idea(self) -> float:
        """
        My assumption how to calc length of the generated conn in IDEA
        to check moment on the end of the chord

        """
        theta = self.conn_setup.c_angle
        theta_r = (theta * math.pi / 180)

        if self.conn_setup.conn_type[:3] == 'CHS':
            d_0 = self.conn_setup.chord.d
            d_1 = self.conn_setup.conn_member.d
            t0 = self.conn_setup.chord.t


            if theta != 90:

                length_of_end = ((d_0 *0.5) / math.tan(theta_r)) + ((d_1 *0.5) / math.sin(theta_r)) + (d_0 - t0*(3/5)) * 1.25

            else:
                length_of_end = (((d_1 * 0.5) / math.sin(theta_r)) + (d_0 - t0 * (3 / 5)) * 1.25)


        elif self.conn_setup.conn_type[:3] == 'RHS':

            h_0 = self.conn_setup.chord.get_base('h', 0)
            h_1 = self.conn_setup.conn_member.get_base('h', 0)
            t0 = self.conn_setup.chord.t
            theta = self.conn_setup.c_angle

            if theta != 90:
                length_of_end = ((h_0 *0.5) / math.tan(theta_r)) + ((h_1 *0.5) / math.sin(theta_r)) + (h_0 - t0*(3/5)) * 1.25

            else:
                length_of_end = ((h_1 * 0.5) / math.sin(theta_r)) + (h_0 - t0 * (3 / 5)) * 1.25

        else:
            raise KeyError(f'Cant determine end length, check code {self.conn_setup.conn_type}')


        return length_of_end
