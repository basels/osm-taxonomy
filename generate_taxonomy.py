import argparse
import random
import json
import warnings
from osm_taxonomy import *
warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED)
tqdm.pandas()


# -------- main --------------


def main(args):

    # blacklist filtering (default)
    blacklist = DEFAULT_BAD_OSM_TAGS

    if args.blacklist is not None:
        log.info(f'Loading additional terms to ignore (from file {args.blacklist})...')
        with open(args.blacklist, 'r') as file:
            additional_blacklist = set(file.read().splitlines())
            blacklist.extend(additional_blacklist)

    log.info(f'  the following tags will be ignored: {blacklist}')

    # load data
    if args.input != None:
        log.info(f'Loading OSM (xml) file {args.input}...')
        g_osm_data = get_osm_dictionary_from_xml(args.input, blacklist)

    g_osm_tagged_data = {k: v for (k, v) in g_osm_data.items() if 'tags' in v}
    del g_osm_data

    # counters for taxonomy decisions
    update_global_key_value_tag_counter(g_osm_tagged_data)
    g_new_osm_dict = build_new_structured_osm_dictionary(g_osm_tagged_data, blacklist)
    del g_osm_tagged_data

    # processed data to DataFrame
    g_osm_tagged_map = map(lambda x: (x[0],
                                      x[1]['tags'][MAIN_LABEL], x[1]['tags'][SEC_LABEL], x[1]['tags'][THI_LABEL]),
                           g_new_osm_dict.items())
    g_osm_tagged_df = pd.DataFrame(g_osm_tagged_map, columns=['osm_id', MAIN_LABEL, SEC_LABEL, THI_LABEL])
    g_osm_tagged_df.set_index('osm_id', inplace=True)
    del g_osm_tagged_map

    # generate taxonomy tree from DataFrame
    int_thresh = int(args.threshold)
    log.info(f'Setting minimum threshold={int_thresh}...')
    g_taxo_tree = get_taxo_tree(g_osm_tagged_df, int(args.threshold))

    # example for additional filtering (post renaming)
    # g_taxo_tree.remove_invalid_tags(['unclassified', 'unofficial', 'multipolygon'])

    log.info('Generating taxonomy tree...')
    g_taxo_tree.build_taxonomy_tree()

    # save tree to json file
    log.info(f'Saving to file: {args.output}')
    with open(args.output, "w") as f:
        json.dump(tree_to_dict(g_taxo_tree.tree, 0), f)

    ##### load tree from json file #####
    # with open("tree.json", "r") as f:
    #     tree_dict = json.load(f)
    # taxo_tree = Tree()
    # dict_to_tree(taxo_tree, tree_dict)
    # print(taxo_tree)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically construct a lightweight taxonomy for geographic features using OpenStreetMap (OSM) data.")
    parser.add_argument("--input", type=str, help="OSM dump (xml) input filename.", required=True)
    parser.add_argument("--output", type=str, default='tree.json', help="Taxonomy tree (json) filename.")
    parser.add_argument("--threshold", type=str, default='10', help="Minimum frequency threshold per tag.")
    parser.add_argument("--blacklist", type=str, help="(txt) file with tags to ignore (one per line, as seen on OSM).")

    args = parser.parse_args()
    main(args)
