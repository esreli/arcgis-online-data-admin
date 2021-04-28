from sys import exit
from json import dumps
from arcgis.features import FeatureLayerCollection
from src.environment import *
from src.utils import batch, ResultsReport


@args(LOGGER, CONFIGURATION, DEV)
def main():
    # Build logger
    logger = ENV.LOGGER
    # Build reference to credentialed gis
    gis = ENV.CONFIGURATION.gis

    ###################################################
    #
    # First, we try to build a spatial dataframe from
    # a feature layer hosted in a feature service.
    #
    # If that fails, next we try to build a spatial
    # dataframe from a local shapefile.
    #
    ###################################################
    source_layer = None
    source_sdf = None
    try:
        item_id = ENV.CONFIGURATION.yml['source']['feature-service-item-id']
        layer_index = ENV.CONFIGURATION.yml['source']['layer-index']
        # First try service
        if item_id is not None and layer_index is not None:
            logger.info('Accessing source feature service.')
            item = gis.content.get(item_id)
            service = FeatureLayerCollection.fromitem(item=item)
            if len(service.layers) > layer_index:
                source_layer = service.layers[layer_index]
                logger.info(f'Attempting to create spatial dataframe for {source_layer.properties.name} layer.')
                source_sdf = source_layer.query(where="1=1").sdf
                logger.info(f'Successfully created spatial dataframe for {source_layer.properties.name} layer.')
            del item, service
        del item_id, layer_index
        if source_layer is None or source_sdf is None:
            raise Exception('Configuration file must supply feature service item id and layer index for source.')
    except Exception as e:
        logger.error(e)
        logger.info('Could not build spatial data frame from service source data, exiting.')
        exit(1)

    ###################################################
    #
    # Now we build a credentialed destination feature
    # layer on the same gis (Portal).
    #
    ###################################################
    destination_layer = None
    destination_sdf = None
    try:
        item_id = ENV.CONFIGURATION.yml['destination']['feature-service-item-id']
        layer_index = ENV.CONFIGURATION.yml['destination']['layer-index']
        if item_id is not None and layer_index is not None:
            logger.info('Accessing destination feature service.')
            item = gis.content.get(item_id)
            service = FeatureLayerCollection.fromitem(item=item)
            if len(service.layers) > layer_index:
                destination_layer = service.layers[layer_index]
                logger.info(f'Attempting to create spatial dataframe for {destination_layer.properties.name} layer.')
                destination_sdf = destination_layer.query(where="1=1").sdf
                logger.info(f'Successfully created spatial dataframe for {destination_layer.properties.name} layer.')
            del item, service
        del item_id, layer_index
        if destination_layer is None or destination_sdf is None:
            raise Exception('Configuration file must supply feature service item id and layer index for destination.')
    except Exception as e:
        logger.error(e)
        logger.info('Could not build spatial data frame from service destination data, exiting.')
        exit(1)

    ###################################################
    #
    # Now we validate the schemas.
    #
    # Schemas are valid when the source and destination
    # fields are identical except the destination source
    # has an additional reference id key field
    # that is of type esriFieldTypeInteger.
    #
    ###################################################
    logger.info(f'Validating schemas.')
    destination_reference_id_key = None
    try:
        destination_fields = destination_layer.properties.fields
        reference_field_idx = None
        destination_reference_id_key = ENV.CONFIGURATION.yml['destination']['reference-id-key']
        for index, field in enumerate(destination_fields):
            if field['name'] == destination_reference_id_key and field['type'] == 'esriFieldTypeInteger':
                reference_field_idx = index
                break
        if reference_field_idx is None:
            raise Exception(
                f'Destination table does not contain required int type reference field {destination_reference_id_key}')
        destination_fields.pop(reference_field_idx)
        source_fields = source_layer.properties.fields
        if source_fields != destination_fields:
            raise Exception(
                f'Source and destination schemas do not match.')
        logger.info(f'Schemas are valid.')
    except Exception as e:
        logger.error(e)
        logger.info(f'Failed to validate schemas, exiting.')
        exit(1)

    ###################################################
    #
    # Now we create a reference on destination layer
    # to the feature stored in source.
    #
    ###################################################
    logger.info(f'Creating reference key for {len(source_sdf)} features.')
    try:
        # Trim drop key to 10 characters, the sdf column name limit
        source_oid_key = source_layer.properties.objectIdField[:10]
        has_reference_field = False
        for field in destination_layer.properties.fields:
            if field['name'] == destination_reference_id_key and field['type'] == 'esriFieldTypeInteger':
                has_reference_field = True
                break
        if not has_reference_field:
            raise Exception(f'Destination table does not contain required int reference field {destination_reference_id_key}')
        if source_oid_key is not None and destination_reference_id_key is not None:
            # Create destination reference key column derived from source unique key.
            destination_reference_id_key = destination_reference_id_key[:10]
            source_sdf[destination_reference_id_key] = source_sdf.apply(lambda row: row[source_oid_key], axis=1)
            # Drop the source key column and pandas derived 'index' column.
            cols = [source_oid_key]
            if 'index' in source_sdf.columns:
                cols += 'index'
            source_sdf = source_sdf.drop(columns=cols)
        del source_oid_key
    except Exception as e:
        logger.error(e)
        logger.info(f'Failed to create reference key for {destination_layer.properties.name} features, exiting.')
        exit(1)

    ###################################################
    #
    # Now we perform a batching process that matches
    # reference ID key on source and destination to
    # determine if we need to add, update, or delete
    # records found on source to the destination layer
    #
    ###################################################
    logger.info(f'Batching {len(source_sdf)} staged edits.')
    try:
        destination_oid_key = destination_layer.properties.objectIdField[:10]
        edits = batch(
            source_sdf=source_sdf,
            destination_sdf=destination_sdf,
            destination_oid_key=destination_oid_key,
            destination_reference_id_key=destination_reference_id_key
        )
    except Exception as e:
        logger.error(e)
        logger.info(f'Failed to batch {len(source_sdf)} staged features '
                    f'for {destination_layer.properties.name} layer '
                    f'using key {destination_reference_id_key}, exiting.')
        exit(1)

    ###################################################
    #
    # Now we upload add, update and delete edits
    # to the destination feature layer.
    #
    ###################################################
    logger.info(f'Uploading features: '
                f'({len(edits.add) if edits.add else 0}) adds, '
                f'({len(edits.update) if edits.update else 0}) updates, '
                f'({len(edits.delete) if edits.delete else 0}) deletes.')
    try:
        results = destination_layer.edit_features(
            adds=edits.add,
            updates=edits.update,
            deletes=edits.delete
        )
    except Exception as e:
        logger.error(e)
        logger.info(f'Failed to edit {destination_layer.properties.name} features: '
                    f'({len(edits.add) if edits.add else 0}) adds, '
                    f'({len(edits.update) if edits.update else 0}) updates, '
                    f'({len(edits.delete) if edits.delete else 0}) deletes, exiting.')
        exit(1)

    ###################################################
    #
    # Now we log the results.
    #
    ###################################################
    report = ResultsReport(results)
    del results
    try:
        logger.debug(f'Adds results: {dumps(report.adds, indent=4)}')
        logger.debug(f'Updates results: {dumps(report.updates, indent=4)}')
        logger.debug(f'Delete results: {dumps(report.deletes, indent=4)}')
    except Exception as e:
        logger.error(e)
        logger.error('Could not parse results.')

    logger.info('Finished.')
    exit(0)

if __name__ == '__main__':
    main()