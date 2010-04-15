-- In case of an error, we want to know which command have failed
set echo on;

-- Drop system.mac
ALTER TABLE system DROP CONSTRAINT "SYSTEM_PT_UK";
ALTER TABLE system DROP COLUMN mac;
ALTER TABLE system ADD CONSTRAINT "SYSTEM_PT_UK" UNIQUE (name, dns_domain_id, ip);

-- Add the new fields to hardware_entity
ALTER TABLE hardware_entity ADD label VARCHAR(63);
ALTER TABLE hardware_entity ADD hardware_type VARCHAR(64);

-- Populate hardware_entity.label
UPDATE hardware_entity
	SET label = (SELECT name FROM machine WHERE machine.machine_id = hardware_entity.id)
	WHERE hardware_entity_type = 'machine';
UPDATE hardware_entity
	SET label = (SELECT system.name
			FROM chassis, system
			WHERE chassis.chassis_hw_id = hardware_entity.id AND
				chassis.system_id = system.id)
	WHERE hardware_entity_type = 'chassis_hw';
UPDATE hardware_entity
	SET label = (SELECT system.name
			FROM switch, system
			WHERE switch.switch_id = hardware_entity.id AND
				switch.id = system.id)
	WHERE hardware_entity_type = 'switch_hw';

ALTER TABLE hardware_entity
	MODIFY (label CONSTRAINT "HW_ENT_LABEL_NN" NOT NULL);
-- FIXME
-- SELECT label, hardware_entity_type FROM hardware_entity WHERE label in (SELECT label FROM hardware_entity GROUP BY label HAVING count(*) > 1);
-- Chassis names are apparently not unique:
-- dd950c3 ha476c2 np3c1 dd950c2 dd950c1 ds950c3 oy561c1 ds951c2 ds950c2 ds950c1
-- Full names:
-- dd950c3.ms.com dd950c3.devin1.ms.com ha476c2.ms.com ha476c2.one-nyp.ms.com ha476c2.the-ha.ms.com np3c1.ms.com np3c1.one-nyp.ms.com dd950c2.ms.com dd950c2.devin1.ms.com dd950c1.ms.com dd950c1.devin1.ms.com ds950c3.ms.com ds950c3.devin2.ms.com oy561c1.ms.com oy561c1.heathrow.ms.com ds951c2.ms.com ds951c2.devin2.ms.com ds950c2.ms.com ds950c2.devin2.ms.com ds950c1.ms.com ds950c1.devin2.ms.com
CREATE UNIQUE INDEX "HARDWARE_ENTITY_LABEL_UK" ON hardware_entity(label);

-- Populate hardware_type
UPDATE hardware_entity SET hardware_type = 'machine' WHERE hardware_entity_type = 'machine';
UPDATE hardware_entity SET hardware_type = 'chassis' WHERE hardware_entity_type = 'chassis_hw';
UPDATE hardware_entity SET hardware_type = 'switch' WHERE hardware_entity_type = 'switch_hw';

-- Drop hardware_entity_type and enable non-null check on hardware_type
ALTER TABLE hardware_entity
	DROP COLUMN hardware_entity_type;
ALTER TABLE hardware_entity
	MODIFY (hardware_type CONSTRAINT "HW_ENT_HARDWARE_TYPE_NN" NOT NULL);

-- Drop machine.name
ALTER TABLE machine DROP COLUMN name;

--
-- Make DynamicStub a child of FutureARecord
--
INSERT INTO future_a_record (system_id)
	SELECT system_id FROM dynamic_stub;
ALTER TABLE dynamic_stub DROP CONSTRAINT "DYNAMIC_STUB_SYSTEM_FK";
ALTER TABLE dynamic_stub
	ADD CONSTRAINT "DYNAMIC_STUB_FARECORD_FK" FOREIGN KEY (system_id) REFERENCES future_a_record (system_id) ON DELETE CASCADE;

--
-- Create reserved_name
--
CREATE TABLE reserved_name (
	system_id INTEGER CONSTRAINT "RESERVED_NAME_SYSTEM_ID_NN" NOT NULL,
	CONSTRAINT "RESERVED_NAME_SYSTEM_FK" FOREIGN KEY (system_id) REFERENCES system (id) ON DELETE CASCADE,
	CONSTRAINT "RESERVED_NAME_PK" PRIMARY KEY (system_id)
);

-- Convert old system subclasses to future_a_record/reserved_name
INSERT INTO future_a_record (system_id)
	SELECT id FROM system
		WHERE ip IS NOT NULL AND
			system_type != 'future_a_record' AND
			system_type != 'dynamic_stub';
UPDATE SYSTEM
	SET system_type = 'future_a_record'
	WHERE ip IS NOT NULL AND
		system_type != 'future_a_record' AND
		system_type != 'dynamic_stub';

INSERT INTO reserved_name (system_id)
	SELECT id FROM system
		WHERE ip IS NULL AND system_type != 'reserved_name';
UPDATE system
	SET system_type = 'reserved_name'
	WHERE ip IS NULL AND system_type != 'reserved_name';

--
-- Create primary_name_association
--
CREATE TABLE primary_name_association (
	hardware_entity_id INTEGER CONSTRAINT "PRI_NAME_ASC_HW_ENT_ID_NN" NOT NULL,
	a_record_id INTEGER CONSTRAINT "PRI_NAME_ASC_A_RECORD_ID_NN" NOT NULL,
	creation_date DATE CONSTRAINT "PRI_NAME_ASC_CR_DATE_NN" NOT NULL,
	comments VARCHAR(255),
	CONSTRAINT "PRIMARY_NAME_ASSOCIATION_PK" PRIMARY KEY (hardware_entity_id, a_record_id),
	CONSTRAINT "PRIMARY_NAME_ASC_HW_ENT_UK" UNIQUE (hardware_entity_id),
	CONSTRAINT "PRIMARY_NAME_ASC_DNS_UK" UNIQUE (a_record_id),
	CONSTRAINT "PRIMARY_NAME_ASC_HW_FK" FOREIGN KEY (hardware_entity_id) REFERENCES hardware_entity (id),
	CONSTRAINT "PRIMARY_NAME_ASC_A_REC_FK" FOREIGN KEY (a_record_id) REFERENCES future_a_record (system_id) ON DELETE CASCADE
);

QUIT;
