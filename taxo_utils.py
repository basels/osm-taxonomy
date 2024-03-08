import socket
import logging
import lxml.etree
import pandas as pd
from copy import deepcopy
from time import time
from datetime import datetime, timedelta
from sys import stdout
from os.path import getsize
from tqdm import tqdm
from collections import Counter
from treelib import Node, Tree

DEFAULT_BAD_OSM_TAGS = ['source', 'name', 'created_by', 'description', 'email', 'phone', 'yes', 'no']
MAIN_LABEL = 'label'
SEC_LABEL = 'ihi_others'
THI_LABEL = 'nhi_others'

g_k_v_counter = Counter()

# ----------- logging -----------

hostname = socket.gethostname()
logging.basicConfig(filename=f'log_{hostname}__{datetime.now().strftime("%Y_%m_%d.%H_%M_%S")}.log',
                    filemode='w',
                    level=logging.INFO, # .DEBUG
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

log = logging.getLogger(__name__)

# ----------- xml parser --------

def bytes_to_human(size):
    ''' Returns a human readable file size from a number of bytes. '''

    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']:
        if size < 1024: break
        size /= 1024
    return '%.2f%sB' % (size, unit)


def seconds_to_human(seconds):
    ''' Returns a human readable string from a number of seconds. '''

    return str(timedelta(seconds=int(seconds))).zfill(8)


def print_xml_parsing_progress(bytes_processed, total_bytes, start_time):
    """Display the progress of XML parsing."""

    percent = bytes_processed / total_bytes
    bar = ('█' * int(percent * 32)).ljust(32)
    time_delta = time() - start_time
    eta = seconds_to_human((total_bytes - bytes_processed) * time_delta / bytes_processed)
    avg_speed = bytes_to_human(bytes_processed / time_delta).rjust(9)
    stdout.flush()
    stdout.write('\r  %6.02f%% |%s| %s/s eta %s' % (100 * percent, bar, avg_speed, eta))


def get_osm_dictionary_from_xml(osm_filename, bad_osm_tags=DEFAULT_BAD_OSM_TAGS, get_geodata=False):
    """Extracts OpenStreetMap data from an XML file into a dictionary."""

    osm_data = {}
    total_bytes = getsize(osm_filename)
    start_time = time()

    with open(osm_filename, 'rb') as f:
        context = lxml.etree.iterparse(f, events=('start',))
        item_id = None

        for idx, (_, elem) in enumerate(context):

            # Print progress every 10,000 elements to reduce stdout writes.
            # Adjust this number based on your needs.
            if idx % 10000 == 0:
                print_xml_parsing_progress(f.tell(), total_bytes, start_time)

            # Node parsing
            if elem.tag in ('node', 'way', 'relation'):
                item_id = elem.tag + '/' + elem.attrib['id']
                osm_data.setdefault(item_id, {})
                if get_geodata is True and elem.tag == 'node':
                    if item_id not in osm_data.keys():
                        # add node to dict, set: lat, lon (next we add tags)
                        osm_data[item_id] = {'lat': elem.attrib['lat'], 'lon': elem.attrib['lon']}

            # Tag parsing
            elif elem.tag == 'tag' and item_id in osm_data:
                tag_key = elem.attrib['k']
                tag_val = elem.attrib['v']

                if (tag_key.lower() not in bad_osm_tags) and (':' not in tag_key) and \
                        (tag_val.lower() not in bad_osm_tags) and (':' not in tag_val):
                    osm_data[item_id].setdefault('tags', {})[tag_key] = tag_val

            elem.clear()

    return osm_data


# ----------- general -----------


def update_global_key_value_tag_counter(tagged_data_dict):
    global g_k_v_counter

    for itm_id, itm_dict in tqdm(tagged_data_dict.items(), total=len(tagged_data_dict)):
        '''
        example of a tagged way ('way/3087669') in g_osm_data
        {..., 'tags': {'highway': 'service', 'service': 'driveway'}}
        '''
        for k, v in itm_dict['tags'].items():
            g_k_v_counter[':'.join([k, v])] += 1


def get_osm_types_from_object(osm_object_dict, bad_osm_tags=DEFAULT_BAD_OSM_TAGS):
    """ returns a dictionary with main label and disqualified labels:
        {'label': 'A3', 'ihi_others': ['A1', 'A2'] 'nhi_others': ['B', 'C']}

        example: input: {'tags': {'highway': 'service', 'service': 'driveway', 'waterway': 'stream', 'lanes': '2'}}
                 output: {'label': 'driveway', 'ihi_others': ['highway', 'service'], 'nhi_others': ['waterway:stream', 'lanes:2']}

                 ## note the the order of output labels in 'nhi_others' is according to their frequency in the data:
                    [('waterway:stream', 71918), ('lanes:2', 55562)]"""

    global g_k_v_counter

    ret_dict = {MAIN_LABEL: '', SEC_LABEL: [], THI_LABEL: []}

    if 'tags' in osm_object_dict.keys():

        itm_orig_tags = osm_object_dict['tags']
        itm_tags_cpy1 = deepcopy(itm_orig_tags)

        # --------- cleanup bad tags -----------------

        # first let's get rid of bad tags
        # and get rid of duplicates (key == value)
        #    {'leisure': 'swimming_pool', 'swimming_pool': 'swimming_pool'}
        #    {'government': 'government', 'office': 'government'}
        for k, v in itm_orig_tags.items():
            if (k.lower() in bad_osm_tags) or (':' in k) or \
                    (v.lower() in bad_osm_tags) or (':' in v) or \
                    (k.lower() == v.lower()) or (v.isnumeric()):
                del itm_tags_cpy1[k]

        # --------- construct hierarchical tags ------

        itm_tags_cpy2 = deepcopy(itm_tags_cpy1)
        itm_removed_keys = []

        # if a label (k1) value (v1) is equal to another key (k2=v1), remove the key (k1)
        # example: 'tags': {'highway': 'service', 'service': 'driveway'} --> 'service' is removed
        most_granular_so_far = None  # should be `driveway` for the example above
        for k, v in itm_tags_cpy1.items():
            if v in itm_tags_cpy2.keys():
                most_granular_so_far = v
                itm_removed_keys.append(k)
                del itm_tags_cpy2[k]

        # move the most granular one ('driveway' --> 'service' --> 'highway')
        if most_granular_so_far:
            ret_dict[MAIN_LABEL] = itm_tags_cpy1[most_granular_so_far]  # we need to take the value of this key
            itm_removed_keys.append(most_granular_so_far)
            del itm_tags_cpy2[most_granular_so_far]
            ret_dict[SEC_LABEL] = itm_removed_keys

        # if there are more tags that are disconnected (not part of the hierarchy), keep them aside
        if len(itm_tags_cpy2.keys()) > 0:
            mini_dict = Counter()
            for k, v in itm_tags_cpy2.items():
                gkv_comparison_key = ':'.join([k, v])
                mini_dict[gkv_comparison_key] = g_k_v_counter[gkv_comparison_key]

            ret_dict[THI_LABEL] = [x[0] for x in mini_dict.most_common()]

        # we finished constructing the prelim dict, now we need to re-check to return a valid dict
        # if there's nothing in MAIN_LABEL, take the first element in THI_LABEL and split to key:value
        #    (value goes to MAIN_LABEL, kay goes to SEC_LABEL)
        if len(ret_dict[MAIN_LABEL]) == 0 and len(ret_dict[THI_LABEL]) > 0:
            most_common_sub_label_and_val = ret_dict[THI_LABEL].pop(0)
            label_split = most_common_sub_label_and_val.split(':')
            ret_dict[SEC_LABEL], ret_dict[MAIN_LABEL] = most_common_sub_label_and_val.split(':')

    return ret_dict


def build_new_structured_osm_dictionary(tagged_data_dict, bad_osm_tags=DEFAULT_BAD_OSM_TAGS):
    new_dict = {}
    for itm_id, itm_dict in tqdm(tagged_data_dict.items(), total=len(tagged_data_dict)):
        new_dict[itm_id] = deepcopy(itm_dict)
        new_dict[itm_id]['tags'] = get_osm_types_from_object(itm_dict, bad_osm_tags)
    return new_dict


# ----------- tree ----------


def tree_to_dict(tree, node_id):
    node = tree.get_node(node_id)
    children = tree.children(node_id)
    node_dict = {"name": node.tag, "children": []}
    for child in children:
        node_dict["children"].append(tree_to_dict(tree, child.identifier))
    return node_dict


def dict_to_tree(tree, node_dict, parent_id=None):
    node_id = node_dict["name"]
    tree.create_node(node_dict["name"], node_id, parent=parent_id)
    for child_dict in node_dict["children"]:
        dict_to_tree(tree, child_dict, node_id)


def get_path_of_labels(main_label, other_labels):
    """input:  main_label=driveway, other_labels=[highway, service]
    output: highway--service--driveway"""

    if not isinstance(other_labels, list):
        other_labels = [other_labels]

    path_string = ""
    for parent_label in other_labels:
        path_string = path_string + str(parent_label) + "--"
    path_string += str(main_label)

    return path_string


class OSMPathCounter():
    def __init__(self):
        self.g_path_strings_cntr = Counter()

    def count_path_of_labels(self, main_label, other_labels):
        """example of updated g_path_strings_cntr (global var)
                Counter({'highway--residential': 305244,
                         'highway--tertiary': 19096,
                         'highway--service--driveway': 135571 ...})
        -------
        example run:
        _ = [count_path_of_labels(x, y) for x, y in tqdm(zip(g_df_ways_sample['label'], g_df_ways_sample['hi_labels']), total=len(g_df_ways_sample))]
        -------"""
        path_string = get_path_of_labels(main_label, other_labels)
        self.g_path_strings_cntr[path_string] += 1

    def get_osm_tag_parent_child_counters(self):
        # split each counter to 1+ tuples:
        #   highway--residential: 305244 --> (highway, residential, 305244)
        #   highway--service--driveway: 135571 --> (highway, service, 135571), (service, driveway, 135571)

        osmtag_tuples_counter = Counter()
        for pcnt_str, pcnt_val in self.g_path_strings_cntr.items():
            pstr_elements = pcnt_str.split('--')
            num_of_eles = len(pstr_elements)
            for idx, _ in enumerate(pstr_elements):
                if idx + 1 < num_of_eles:
                    osmtag_tuples_counter[(pstr_elements[idx], pstr_elements[idx + 1])] += pcnt_val
        return osmtag_tuples_counter


def get_osm_tag_parent_child_data_as_df(osm_tags_tuples_counter):
    list_of_osmtag_tuples = []
    for cnt_name, cnt_val in osm_tags_tuples_counter.items():
        list_of_osmtag_tuples.append((cnt_name[0], cnt_name[1], cnt_val))
    osmtagsdf = pd.DataFrame(list_of_osmtag_tuples, columns=['parent', 'child', 'counter']).sort_values(by='counter', ascending=False)
    return osmtagsdf


class OSMTaxonomyNode(object):
    def __init__(self, id, label, counter):
        self.id = id
        self.label = label
        self.counter = counter
        color = '33'
        if self.counter:
            color = '35'
        self.print_str = f'{self.label} \033[{color}m[{self.counter}]\033[0m'


class OSMTaxonomyTree():
    def __init__(self, osm_tags_dataframe, min_counter_per_relation=1):
        self.osmdf = osm_tags_dataframe
        self.osmdf = self.osmdf[self.osmdf['counter'] >= min_counter_per_relation]
        self.osmdf.reset_index()
        self.tree = None

    def remove_invalid_tags(self, tags_to_ignore):
        tags_to_ignore = set(tags_to_ignore)
        non_leaves = tags_to_ignore.intersection(set(self.osmdf['parent']))
        if len(non_leaves) > 0:
            log.info(f'[WARNING] removing non-leaf tags: {non_leaves}')
            self.osmdf = self.osmdf[~self.osmdf['parent'].isin(non_leaves)]
        leaves = tags_to_ignore.intersection(set(self.osmdf['child']))
        if len(leaves) > 0: log.info(f'removing leaf tags: {leaves}')
        self.osmdf = self.osmdf[~self.osmdf['child'].isin(leaves)]
        fine_grained_tags_to_ignore = [k for k in tags_to_ignore if '__' in k]
        if len(fine_grained_tags_to_ignore) > 0: log.info(f'removing fine_grained_tags: {fine_grained_tags_to_ignore}')
        for itm in fine_grained_tags_to_ignore:
            self.osmdf = self.osmdf.drop(self.osmdf[self.osmdf['child'] == itm.split('__')[0]]
                                         [self.osmdf['parent'] == itm.split('__')[1]].index)
        return

    def get_tags_on_path_to_tags(self, target_tag):
        tags_on_path = [target_tag]
        curr_parent = self.tree.parent(target_tag).identifier
        while curr_parent != 0:
            tags_on_path.append(curr_parent)
            curr_parent = self.tree.parent(curr_parent).identifier
        return tags_on_path

    def get_all_tags_in_tree(self):
        return [k.identifier for k in self.tree.all_nodes_itr() if k.identifier != 0]

    def add_taxo_node(self, id, label, counter=None, parent=None):
        node = OSMTaxonomyNode(id, label, counter)
        self.tree.create_node(tag=id, identifier=id, data=node, parent=parent)

    def build_taxonomy_tree(self):
        tag_keys = set(self.osmdf['parent'].unique())
        tag_values = set(self.osmdf['child'].unique())
        # all tag keys and values
        alltags = tag_keys.union(tag_values)

        self.tree = Tree()
        self.add_taxo_node(0, 'osm')

        # Creating nodes under root
        for itm in alltags:
            # self.tree.create_node(itm, itm, parent=0)
            itm_counter = None
            if len(self.osmdf[self.osmdf['child'] == itm]) == 1:
                itm_counter = int(self.osmdf[self.osmdf['child'] == itm].counter)
            self.add_taxo_node(itm, itm, counter=itm_counter, parent=0)

        node_ids_to_delete = []

        # Creating nodes under root
        for _, c in self.osmdf.iterrows():
            if self.tree.get_node(c["child"]):
                # node exists in tree (or haven't been changed/renamed)
                curr_parent = self.tree.parent(c["child"]).identifier
                if curr_parent != 0:

                    new_child_node = '__'.join([c["child"], c["parent"]])
                    self.add_taxo_node(new_child_node, new_child_node, counter=c["counter"], parent=c["parent"])

                    renamed_child_node = '__'.join([c["child"], curr_parent])
                    if self.tree.get_node(renamed_child_node) is None:
                        rename_counter = int(
                            self.osmdf[self.osmdf['child'] == c['child']][self.osmdf['parent'] == curr_parent].counter)
                        self.add_taxo_node(renamed_child_node, renamed_child_node, counter=rename_counter, parent=curr_parent)
                        # instead of updateding the node, we create a new one & later delete the original, to preserve future conflicts of names
                        #   (residential --> residential__landuse, residential__highway, residential__building)
                        node_ids_to_delete.append(c["child"])

                    log.info(f'\033[35mnode {c["child"]} --> [{new_child_node} (under {c["parent"]}) ' +
                             f'& {renamed_child_node} (under {self.tree.parent(renamed_child_node).identifier})]\033[0m')
                else:
                    self.tree.move_node(c["child"], c["parent"])
            else:
                log.info(f'node {c["child"]} (to be added under {c["parent"]}) is not in the tree')
        for node in node_ids_to_delete:
            self.tree.remove_node(node)
            log.info(f'removed node {node}')

        log.info('*' * 100)
        log.info(self.tree)
        return

    def get_tag_by_level_in_tree(self, ordered_labels, desired_tag_level):
        if len(ordered_labels) > 0:
            main_tag = ordered_labels[-1]
            tag = main_tag
            if not self.tree.contains(tag) and len(ordered_labels) > 1:
                tag = ordered_labels[-1] + '__' + ordered_labels[-2]
            if self.tree.contains(tag):
                real_tag_level = self.tree.level(tag)
                if desired_tag_level == real_tag_level:
                    return tag
                elif desired_tag_level > real_tag_level:
                    return ''
            return self.get_tag_by_level_in_tree(ordered_labels[:-1], desired_tag_level)
        return ''


def get_taxo_tree(input_df, freq_threshold=100):
    osmcounter = OSMPathCounter()
    _ = [osmcounter.count_path_of_labels(x, y) for x, y in
         tqdm(zip(input_df[MAIN_LABEL], input_df[SEC_LABEL]), total=len(input_df))]
    osmtag_tuples_counter = osmcounter.get_osm_tag_parent_child_counters()
    osmtagsdf = get_osm_tag_parent_child_data_as_df(osmtag_tuples_counter)
    return OSMTaxonomyTree(osmtagsdf, freq_threshold)

