# Databricks notebook source
# MAGIC %pip install sqlmodel==0.0.25

# COMMAND ----------

VOLUME_PATH = dbutils.widgets.get("VOLUME_PATH")

# COMMAND ----------

# MAGIC %pip install {VOLUME_PATH}/entities/lakebase_responders_entities*.whl
# MAGIC %restart_python

# COMMAND ----------

from sqlmodel import Session, SQLModel, create_engine, select
from lakebase_responders_entities import Vehicle, Emergency, UrgencyLevel, ServiceType, VehicleType, Plan
from datetime import datetime
import random

# COMMAND ----------

db_user = dbutils.widgets.get("DB_USER")
db_password = dbutils.widgets.get("DB_PASSWORD")
db_host = dbutils.widgets.get("DB_HOST")
db_name = dbutils.widgets.get("DB_NAME")

# COMMAND ----------

engine = create_engine(url=f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:5432/{db_name}")

# COMMAND ----------

SQLModel.metadata.create_all(engine)

# COMMAND ----------

session = Session(engine)

# COMMAND ----------

vehicles_to_create = [
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        registration="B-P 3021",
        capacity=4,
        lat=52.5189,
        lon=13.3982,
    ),
    Vehicle(
        vehicle_type=VehicleType.van,
        service_type=ServiceType.police,
        capacity=9,
        registration="B-P 8812",
        lat=52.5024,
        lon=13.3876,
    ),
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        capacity=4,
        registration="B-P 4590",
        lat=52.5301,
        lon=13.3645,
    ),
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        capacity=4,
        registration="B-P 7118",
        lat=52.5255,
        lon=13.4011,
    ),
    Vehicle(
        vehicle_type=VehicleType.van,
        service_type=ServiceType.police,
        registration="B-P 9253",
        capacity=9,
        lat=52.4998,
        lon=13.3559,
    ),
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        capacity=4,
        registration="B-P 1234",
        lat=52.5167,
        lon=13.3775,
    ),
    Vehicle(
        vehicle_type=VehicleType.van,
        service_type=ServiceType.police,
        capacity=9,
        registration="B-P 5555",
        lat=52.5088,
        lon=13.4103,
    ),
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        capacity=4,
        registration="B-P 2876",
        lat=52.5333,
        lon=13.3899,
    ),
    Vehicle(
        vehicle_type=VehicleType.van,
        service_type=ServiceType.police,
        capacity=9,
        registration="B-P 6709",
        lat=52.5015,
        lon=13.3921,
    ),
    Vehicle(
        vehicle_type=VehicleType.car,
        service_type=ServiceType.police,
        capacity=4,
        registration="B-P 1102",
        lat=52.5204,
        lon=13.3508,
    ),
]

# COMMAND ----------

random.shuffle(vehicles_to_create)
session.add_all(vehicles_to_create[:5])
session.commit()

# COMMAND ----------

emergencies_to_create = [
    Emergency(
        service_type=ServiceType.police,
        transcript="Anrufer meldet einen bewaffneten Raubüberfall in einer Bank. Täter sind noch vor Ort. Dringend Unterstützung anfordern.",
        address="Kurfürstendamm 231, 10719 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.3105,
        lat=52.5025,
        reported=datetime(2025, 9, 18, 14, 30, 15)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Schwerer Verkehrsunfall mit mehreren Fahrzeugen und Verletzten an der Kreuzung. Straße ist blockiert.",
        address="Potsdamer Platz, 10785 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.3757,
        lat=52.5096,
        reported=datetime(2025, 9, 18, 8, 22, 5)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Einbruch in ein Wohnhaus wird gemeldet. Die Bewohner sind im Urlaub. Nachbar hat Glas splittern hören.",
        address="Fasanenstraße 25, 10719 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.3235,
        lat=52.5068,
        reported=datetime(2025, 9, 18, 2, 45, 10)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Ladendetektiv meldet einen aggressiven Ladendieb, der im Büro festgehalten wird. Benötigen dringend eine Streife.",
        address="Leipziger Pl. 12, 10117 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.3768,
        lat=52.5090,
        reported=datetime(2025, 9, 18, 13, 0, 56)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Meldung über Vandalismus. Jugendliche besprühen Wände am S-Bahnhof. Sie sind noch in der Nähe.",
        address="S-Bahnhof Warschauer Straße, 10243 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.4500,
        lat=52.5052,
        reported=datetime(2025, 9, 18, 22, 15, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anwohner beschwert sich über extreme Ruhestörung durch eine Party in der Nachbarwohnung. Keine Reaktion auf Klopfen.",
        address="Oranienstraße 160, 10999 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.4182,
        lat=52.4990,
        reported=datetime(2025, 9, 18, 23, 50, 30)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Falschparker blockiert eine private Einfahrt vollständig. Der Fahrzeughalter ist nicht auffindbar.",
        address="Kastanienallee 50, 10119 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.4109,
        lat=52.5385,
        reported=datetime(2025, 9, 18, 10, 5, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Verdächtige Person schaut seit über einer Stunde in geparkte Autos. Trägt eine dunkle Kapuzenjacke.",
        address="Sonnenallee 220, 12059 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.4542,
        lat=52.4760,
        reported=datetime(2025, 9, 18, 15, 20, 44)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Taschendiebstahl auf dem Marktplatz gemeldet. Das Opfer kann eine gute Beschreibung des Täters geben.",
        address="Marktplatz am Rathaus Schöneberg, 10825 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.3433,
        lat=52.4842,
        reported=datetime(2025, 9, 18, 11, 40, 18)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Öffentliche Auseinandersetzung zwischen zwei Personen, die zu eskalieren droht. Es wird laut geschrien.",
        address="U-Bahnhof Kottbusser Tor, 10999 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.4178,
        lat=52.4990,
        reported=datetime(2025, 9, 18, 16, 0, 5)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anrufer meldet eine vermisste Person. Ein 8-jähriges Kind ist seit 30 Minuten im Tiergarten nicht mehr auffindbar.",
        address="Großer Tiergarten, 10557 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.359,
        lat=52.514,
        reported=datetime(2025, 9, 18, 17, 5, 12)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Beobachtung von Drogenhandel an einer U-Bahn-Station. Mehrere Personen beteiligt. Situation ist angespannt.",
        address="U-Bahnhof Hermannplatz, 10967 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.424,
        lat=52.488,
        reported=datetime(2025, 9, 18, 18, 10, 45)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Tourist meldet den Diebstahl seines Rucksacks mit Reisepass und Wertsachen. Täter ist in der Menschenmenge verschwunden.",
        address="Brandenburger Tor, Pariser Platz, 10117 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.377,
        lat=52.516,
        reported=datetime(2025, 9, 18, 13, 20, 30)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anrufer meldet einen Betrugsversuch. Eine Person gibt sich als Handwerker aus und verlangt überhöhte Barzahlung.",
        address="Hauptstraße 155, 10827 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.351,
        lat=52.488,
        reported=datetime(2025, 9, 18, 11, 35, 22)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Ein LKW-Fahrer hat seine Ladung verloren. Mehrere Kisten blockieren eine Fahrspur auf der Stadtautobahn.",
        address="A113, Höhe Späthstraße, 12359 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.468,
        lat=52.448,
        reported=datetime(2025, 9, 18, 10, 15, 50)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Meldung einer ungenehmigten Demonstration. Etwa 50 Personen versammeln sich und blockieren den Verkehr.",
        address="Frankfurter Allee, 10247 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.477,
        lat=52.515,
        reported=datetime(2025, 9, 18, 16, 40, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Ein Passant hat eine Brieftasche mit Ausweis und Bargeld gefunden und möchte sie bei der Polizei abgeben.",
        address="Polizeiabschnitt 53, Friederich-Wilhelm-Str. 64, 12103 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.364,
        lat=52.460,
        reported=datetime(2025, 9, 18, 12, 55, 10)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Bericht über einen häuslichen Streit. Nachbarn hören lautes Schreien und Poltern aus der Wohnung nebenan.",
        address="Gneisenaustraße 20, 10961 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.395,
        lat=52.493,
        reported=datetime(2025, 9, 18, 20, 30, 5)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Autofahrer meldet einen aggressiven Drängler auf der Autobahn. Fahrzeug hat mehrfach gefährlich überholt.",
        address="A115, Höhe Dreieck Funkturm, 14057 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.279,
        lat=52.508,
        reported=datetime(2025, 9, 18, 9, 5, 40)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anruf wegen eines Cybercrime-Vorfalls. Das Computersystem einer kleinen Firma wurde gehackt und gesperrt.",
        address="Karl-Marx-Straße 90, 12043 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.436,
        lat=52.482,
        reported=datetime(2025, 9, 18, 14, 50, 21)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anrufer meldet Schüsse in einem Innenhof. Panische Schreie im Hintergrund. Mehrere Personen flüchten.",
        address="Skalitzer Str. 30, 10999 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.421,
        lat=52.501,
        reported=datetime(2025, 9, 18, 17, 55, 18)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Meldung über einen illegalen Straßenrennen auf der Avus. Mehrere hochmotorisierte Fahrzeuge beteiligt.",
        address="A115 (AVUS), 14055 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.251,
        lat=52.483,
        reported=datetime(2025, 9, 18, 2, 10, 5)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anonymer Anruf über eine Bombendrohung in der Mall of Berlin. Evakuierung wird empfohlen.",
        address="Mall of Berlin, Leipziger Platz 12, 10117 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.377,
        lat=52.509,
        reported=datetime(2025, 9, 18, 14, 2, 30)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Einbruch in ein Juweliergeschäft. Die Alarmanlage wurde ausgelöst, die Täter sind flüchtig.",
        address="Friedrichstraße 80, 10117 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.388,
        lat=52.511,
        reported=datetime(2025, 9, 18, 4, 15, 21)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Fahrerflucht nach einem Unfall mit Personenschaden. Ein Radfahrer wurde angefahren und der PKW ist weitergefahren.",
        address="Danziger Str. 50, 10435 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.430,
        lat=52.537,
        reported=datetime(2025, 9, 18, 12, 40, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Eine Person meldet, dass sie verfolgt und bedroht wird. Sie hat sich in einem Geschäft eingeschlossen.",
        address="Tauentzienstraße 9, 10789 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.336,
        lat=52.502,
        reported=datetime(2025, 9, 18, 16, 5, 11)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Mitarbeiter einer Bank meldet einen Kunden, der versucht, offensichtlich gefälschte Geldscheine einzuzahlen.",
        address="Sparkasse, Karl-Marx-Allee 70, 10243 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.440,
        lat=52.515,
        reported=datetime(2025, 9, 18, 11, 25, 43)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Entdeckung eines manipulierten Geldautomaten. Ein Skimming-Gerät wurde von einem Kunden gefunden.",
        address="Kantstraße 100, 10627 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.305,
        lat=52.508,
        reported=datetime(2025, 9, 18, 15, 0, 50)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anwohner meldet den Diebstahl von zwei hochwertigen Fahrrädern aus einem verschlossenen Keller.",
        address="Boxhagener Str. 25, 10245 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.468,
        lat=52.508,
        reported=datetime(2025, 9, 18, 7, 30, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Hausverwaltung meldet eine unrechtmäßige Besetzung einer leerstehenden Wohnung im Gebäude.",
        address="Rigaer Str. 94, 10247 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.465,
        lat=52.518,
        reported=datetime(2025, 9, 18, 9, 45, 15)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Betreiber eines Kiosks meldet eine Gruppe Jugendlicher, die Kunden belästigen und nicht gehen wollen.",
        address="U-Bahnhof Mehringdamm, 10961 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.389,
        lat=52.493,
        reported=datetime(2025, 9, 18, 17, 10, 29)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Eine vermisste Person wurde gemeldet. Ein 78-jähriger Mann mit Demenz hat seine Wohnung verlassen.",
        address="Bismarckstraße 20, 10627 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.308,
        lat=52.511,
        reported=datetime(2025, 9, 18, 13, 1, 1)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Anruf wegen Tierschutz. Ein Hund ist in einem überhitzten Auto auf einem Parkplatz eingeschlossen.",
        address="Parkplatz IKEA, Landsberger Allee 364, 10365 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.499,
        lat=52.535,
        reported=datetime(2025, 9, 18, 14, 45, 55)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Sicherheitsdienst eines Museums meldet eine Person, die versucht, eine Absperrung zu überwinden.",
        address="Pergamonmuseum, Bodestraße 1-3, 10178 Berlin",
        urgency=UrgencyLevel.medium,
        lon=13.397,
        lat=52.521,
        reported=datetime(2025, 9, 18, 12, 12, 12)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Wohlfahrtscheck angefordert für einen Nachbarn, der seit mehreren Tagen nicht gesehen wurde und nicht auf Anrufe reagiert.",
        address="Wilmersdorfer Str. 50, 10627 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.303,
        lat=52.508,
        reported=datetime(2025, 9, 18, 10, 30, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Meldung über illegale Müllentsorgung. Ein LKW lädt Bauschutt in einem Waldgebiet ab.",
        address="Grunewald, Nähe Havelchaussee, 14193 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.235,
        lat=52.480,
        reported=datetime(2025, 9, 18, 6, 40, 19)
    ),
    # Emergency(
    #     service_type=ServiceType.police,
    #     transcript="Taxifahrer meldet einen Fahrgast, der sich weigert zu zahlen und aggressiv wird.",
    #     address="Hauptbahnhof, Europaplatz 1, 10557 Berlin",
    #     urgency=UrgencyLevel.low,
    #     lon=13.369,
    #     lat=52.525,
    #     reported=datetime(2025, 9, 18, 3, 5, 25)
    # ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Beschwerde über Drohnenflug über einem Wohngebiet, die Privatsphäre der Anwohner wird verletzt.",
        address="Schillerpromenade, 12049 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.424,
        lat=52.482,
        reported=datetime(2025, 9, 18, 16, 20, 0)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Verstoß gegen das Waffengesetz. Eine Person trägt öffentlich ein großes Messer sichtbar am Gürtel.",
        address="Alexanderplatz, 10178 Berlin",
        urgency=UrgencyLevel.high,
        lon=13.413,
        lat=52.522,
        reported=datetime(2025, 9, 18, 15, 33, 44)
    ),
    Emergency(
        service_type=ServiceType.police,
        transcript="Meldung einer Sachbeschädigung. Autoreifen wurden an mehreren Fahrzeugen in einer Straße zerstochen.",
        address="Urbanstraße 70, 10967 Berlin",
        urgency=UrgencyLevel.low,
        lon=13.415,
        lat=52.492,
        reported=datetime(2025, 9, 18, 5, 50, 13)
    )
]

# COMMAND ----------

# random.shuffle(emergencies_to_create)
# session.add_all(emergencies_to_create[:25])
session.add_all(emergencies_to_create)
session.commit()

# COMMAND ----------

dbutils.jobs.taskValues.set(key="DB_URL", value=f"{engine.url.render_as_string(hide_password=False)}")

# COMMAND ----------

engine.dispose()

# COMMAND ----------

dbutils.notebook.exit("0")

# COMMAND ----------

dbutils.widgets.text("DB_USER", "")
dbutils.widgets.text("DB_PASSWORD", "")
dbutils.widgets.text("DB_HOST", "")
dbutils.widgets.text("DB_NAME", "responders")
dbutils.widgets.text("VOLUME_PATH", "")