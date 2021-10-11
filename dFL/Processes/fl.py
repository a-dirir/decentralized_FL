from time import time
from copy import deepcopy


class Aggregation:
    def __init__(self, num_blocks: int, num_nodes: int, min_num_workers: int = 2):
        self.min_num_workers = min_num_workers
        self.num_blocks = num_blocks
        self.num_nodes = num_nodes
        self.aggregation = {i: [] for i in range(num_blocks)}
        self.correct_hash = {i: "" for i in range(num_blocks)}
        self.lookup = {}
        self.honest_aggregators = {i: [] for i in range(self.num_blocks)}

    def update_aggregation_result(self, block_num, aggregation_hash, node_id):
        if self.lookup.get(node_id) is None:
            self.lookup[node_id] = {block_num: len(self.aggregation[block_num])}
            self.aggregation[block_num] += [aggregation_hash]
        elif self.lookup[node_id].get(block_num) is None:
            self.lookup[node_id][block_num] = len(self.aggregation[block_num])
            self.aggregation[block_num] += [aggregation_hash]
        else:
            index = self.lookup[node_id][block_num]
            self.aggregation[block_num][index] = aggregation_hash


    def get_num_workers(self, block_num):
        if len(self.aggregation[block_num]) < self.min_num_workers:
            return self.min_num_workers
        else:
            return self.find_majority(block_num)

    def find_majority(self, block_num):
        tmp = {}
        max_occurrences = 0
        most_hash_occurred = ''
        for aggregation_hash in self.aggregation[block_num]:
            if tmp.get(aggregation_hash) is None:
                tmp[aggregation_hash] = 1
            else:
                tmp[aggregation_hash] += 1

            if tmp[aggregation_hash] > max_occurrences:
                max_occurrences = tmp[aggregation_hash]
                most_hash_occurred = aggregation_hash

        count_max_occurrences = 0
        for aggregation_hash, occurrences in tmp.items():
            if occurrences == max_occurrences:
                count_max_occurrences += 1

        if count_max_occurrences == 1:
            self.correct_hash[block_num] = most_hash_occurred
            return len(self.aggregation[block_num])
        else:
            return min(self.num_nodes, len(self.aggregation[block_num]) + 1)

    def remove_dropouts(self, dropouts: list):
        for dropped_node in dropouts:
            for block_num, index in self.lookup[dropped_node].items():
                self.aggregation[block_num].remove(self.aggregation[block_num][index])

                for node in self.lookup:
                    if self.lookup[node].get(block_num) is not None and self.lookup[node][block_num] > index:
                        self.lookup[node][block_num] -= 1

    def is_all_blocks_done(self):
        if len(self.honest_aggregators[0]) > 0:
            return True

        for block_num, aggregation_hash in self.correct_hash.items():
            if aggregation_hash == '':
                return False

        self.set_honest_aggregators()
        return True

    def set_honest_aggregators(self):
        for node in self.lookup:
            for block_num, index in self.lookup[node].items():
                if self.correct_hash[block_num] == self.aggregation[block_num][index]:
                    self.honest_aggregators[block_num] += [node]


class Group:
    def __init__(self, nodes: list, num_blocks: int, timeout: int):
        self.nodes = nodes
        self.num_blocks = num_blocks
        self.timeout = timeout
        self.blocks = {nodes[i]: {} for i in range(len(nodes))}
        self.blocks_mappings = self.create_mappings(num_blocks)
        self.aggregator = Aggregation(num_blocks, len(nodes))

        current_time = time()
        self.last_update = {nodes[i]: current_time for i in range(len(nodes))}

        self.stage = 1
        self.lookup_stage = {nodes[i]: 1 for i in range(len(nodes))}

        for node_id in nodes:
            self.update_status(node_id, {})

    def create_mappings(self, num_blocks):
        mappings = []
        for block_num in range(num_blocks):
            mappings += [[self.nodes[(block_num + node_index) % len(self.nodes)] for node_index in range(len(self.nodes))]]

        return mappings

    def remove_dropouts(self):
        current_time = time()
        dead_nodes = []
        for node_id, last_update in self.last_update.items():
            if self.last_update[node_id] + self.timeout < current_time:
                dead_nodes += [node_id]

        for node_id in dead_nodes:
            self.nodes.remove(node_id)
            self.last_update.pop(node_id)
            self.blocks.pop(node_id)
            self.lookup_stage.pop(node_id)

        self.aggregator.remove_dropouts(dead_nodes)

    def get_workers(self, block_num: int):
        num_workers = self.aggregator.get_num_workers(block_num)
        if len(self.nodes) < num_workers:
            return []

        count = 0; tmp = []
        for worker in self.blocks_mappings[block_num]:
            if worker in self.nodes:
                tmp += [worker]
                count += 1

            if count >= num_workers:
                break

        return tmp

    def update_blocks(self, node_id: int, completed_blocks: dict):
        self.last_update[node_id] = int(time())

        for block_num, result in completed_blocks.items():
            self.aggregator.update_aggregation_result(block_num, result['aggregation_hash'], node_id)

        for block_num in range(self.num_blocks):
            block_mapping = self.get_workers(block_num)
            if node_id in block_mapping:
                if self.blocks[node_id].get(block_num) is None or completed_blocks.get(block_num) is None:
                    self.blocks[node_id][block_num] = deepcopy(self.nodes)
                else:
                    remaining_nodes = []
                    for sender in self.blocks[node_id][block_num]:
                        if sender not in completed_blocks[block_num]['senders'] and sender in self.nodes:
                            remaining_nodes.append(sender)
                    self.blocks[node_id][block_num] = remaining_nodes

    def update_status(self, node_id: int, completed_blocks: dict):
        self.remove_dropouts()
        if self.last_update.get(node_id) is None:
            return {"stage": -1, "Error": "timeout"}

        if len(self.nodes) < 3:
            return {"stage": -1, "Error": "Number of nodes is not enough"}

        self.update_blocks(node_id, completed_blocks)

        if self.stage == 1:
            if self.is_all_blocks_done():
                self.stage = 2
                return {"stage": 2, "nodes": self.nodes}
            else:
                return {"stage": 1, "blocks": self.blocks[node_id]}

        elif self.stage == 2:
            if self.lookup_stage[node_id] == 1:
                self.lookup_stage[node_id] = 2
                return {"stage": 2, "nodes": self.nodes}
            else:
                if self.aggregator.is_all_blocks_done():
                    aggregated_blocks = {}
                    for i in range(self.num_blocks):
                        if node_id not in self.aggregator.honest_aggregators[i]:
                            index = node_id % len(self.aggregator.honest_aggregators[i])
                            aggregated_blocks[(i+1000)] = [self.aggregator.honest_aggregators[i][index]]

                    return {"stage": 3, "Hashes": self.aggregator.aggregation,"blocks": aggregated_blocks}
                else:
                    return {"stage": 2, "blocks": self.blocks[node_id]}

    def is_all_blocks_done(self):
        for node_id in self.blocks:
            for block_num in self.blocks[node_id]:
                if len(self.blocks[node_id][block_num]) > 0:
                    return False
        return True


class FL:
    def __init__(self, process_id, info, nodes):
        self.process_id = process_id
        self.nodes = nodes
        self.num_blocks = info['num_blocks']
        self.timeout = info['timeout']
        self.file_extension = info['file_extension']
        self.lookup_nodes = {}
        self.groups = []
        self.groups = self.create_groups(self.num_blocks)

    def create_groups(self, num_nodes_per_group: int):
        groups = []
        num_groups = int(len(self.nodes) / num_nodes_per_group)
        for i in range(num_groups):
            start = i * num_nodes_per_group
            end = start + num_nodes_per_group
            if end + num_nodes_per_group >= len(self.nodes):
                end = len(self.nodes)

            group_member = self.nodes[start:end]
            for node in group_member:
                self.lookup_nodes[node] = i

            groups.append(Group(group_member, self.num_blocks, self.timeout))

        return groups

    def update_status(self, node_id: int, completed_blocks: dict):
        group_index = self.lookup_nodes[node_id]
        scheduled_blocks = self.groups[group_index].update_status(node_id, completed_blocks)

        if scheduled_blocks['stage'] > 0:
            scheduled_blocks['requester_id'] = node_id
            scheduled_blocks['process_id'] = self.process_id
            scheduled_blocks['file_extension'] = self.file_extension

        return scheduled_blocks

