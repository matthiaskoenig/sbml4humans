"""Resources of sbml4humans: the example models served by the api.

The models are the example models and the first curated biomodels, the xslt
stylesheets render the math of the report.
"""

from pathlib import Path


RESOURCES_DIR = Path(__file__).parent

# stylesheets of the content MathML -> presentation MathML -> latex conversion
XSLT_DIR = RESOURCES_DIR / "xslt"

# -------------------------------------------------------------------------------------
# COMBINE archives
# -------------------------------------------------------------------------------------
OMEX_DIR = RESOURCES_DIR / "omex"
OMEX_ICGMODEL = OMEX_DIR / "icg_model.omex"
OMEX_OMEPRAZOLEMODEL = OMEX_DIR / "omeprazole_model.omex"
OMEX_COMPMODELS = OMEX_DIR / "CompModels.omex"
OMEX_SHOWCASE = OMEX_DIR / "CombineArchiveShowCase.omex"

API_EXAMPLES_OMEX: list[Path] = [
    OMEX_ICGMODEL,
    OMEX_OMEPRAZOLEMODEL,
    OMEX_COMPMODELS,
    OMEX_SHOWCASE,
]

# -------------------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------------------
MODELS_DIR = RESOURCES_DIR / "models"
REPRESSILATOR_SBML = MODELS_DIR / "repressilator" / "BIOMD0000000012_urn.xml"
GLUCOSE_SBML = MODELS_DIR / "glucose" / "Hepatic_glucose_3.xml"

# hierarchical models (comp), the body models reference their submodels by
# relative path, so the files of a model family stay in one directory
COMP_DIR = MODELS_DIR / "comp"
COMP_ICG_BODY_FLAT = COMP_DIR / "icg_body_flat.xml"
COMP_ICG_BODY = COMP_DIR / "icg_body.xml"
COMP_ICG_LIVER = COMP_DIR / "icg_liver.xml"
COMP_DEX_BODY = COMP_DIR / "dex_body.xml"
COMP_DEX_BODY_FLAT = COMP_DIR / "dex_body_flat.xml"
COMP_DEX_CYP2D6 = COMP_DIR / "cyp2d6.xml"
COMP_DEX_INTESTINE = COMP_DIR / "dex_intestine.xml"
COMP_DEX_KIDNEY = COMP_DIR / "dex_kidney.xml"
COMP_DEX_LIVER = COMP_DIR / "dex_liver.xml"
COMP_SPT_LIVER = COMP_DIR / "spt_liver.xml"
COMP_SPT_INTESTINE = COMP_DIR / "spt_intestine.xml"
COMP_SPT_KIDNEY = COMP_DIR / "spt_kidney.xml"
COMP_SPT_BODY_FLAT = COMP_DIR / "spt_body_flat.xml"
COMP_SPT_BODY = COMP_DIR / "spt_body.xml"

# constraint based models (fbc)
FBC_DIR = MODELS_DIR / "fbc"
FBC_ECOLI_CORE_SBML = FBC_DIR / "e_coli_core.xml.gz"
FBC_RECON3D_SBML = FBC_DIR / "Recon3D.xml.gz"

# small example models, one per SBML feature
EXAMPLES_DIR = RESOURCES_DIR / "examples"
EXAMPLE_IDS: list[str] = [
    "algebraic_rule",
    "annotation",
    "assignment",
    "comp_deletion",
    "constraint_event",
    "distrib_comp",
    "distrib_comp_flat",
    "distrib_distributions",
    "distrib_uncertainties",
    "fbc_example",
    "fbc_mass_charge",
    "linear_chain",
    "minimal_model",
    "minimal_model_comp",
    "minimal_model_comp_flat",
    "model_composition",
    "model_definitions",
    "multiple_substance_units",
    "notes",
    "parameter",
    "random_network",
    "reaction",
    "reaction_with_units",
    "species",
    "unit_definitions",
    "units_namespace",
]

API_EXAMPLES_MODEL: list[Path] = [
    REPRESSILATOR_SBML,
    COMP_ICG_BODY_FLAT,
    COMP_ICG_BODY,
    COMP_ICG_LIVER,
    GLUCOSE_SBML,
    COMP_DEX_BODY,
    COMP_DEX_BODY_FLAT,
    COMP_DEX_CYP2D6,
    COMP_DEX_INTESTINE,
    COMP_DEX_KIDNEY,
    COMP_DEX_LIVER,
    COMP_SPT_LIVER,
    COMP_SPT_INTESTINE,
    COMP_SPT_KIDNEY,
    COMP_SPT_BODY_FLAT,
    COMP_SPT_BODY,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
    *(EXAMPLES_DIR / f"{eid}.xml" for eid in EXAMPLE_IDS),
]

# -------------------------------------------------------------------------------------
# Curated biomodels
# -------------------------------------------------------------------------------------
# the archives of the first curated biomodels (BIOMD0000000001, ...)
BIOMODELS_CURATED_PATH = RESOURCES_DIR / "biomodels"
