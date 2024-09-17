import constants


def simple_search(self):        
        nw, sw, ne, se = 0, 0, 0, 0

        cur_pos = self.player_map.get_cur_pos()
        cur_pos_i, cur_pos_j = cur_pos[0], cur_pos[1]
        for i in range(self.radius):
            for j in range(self.radius):
                if self.player_map.get_seen_counts([[cur_pos_i-i, cur_pos_j-j]])[0]>0:
                    nw += 1
                if self.player_map.get_seen_counts([[cur_pos_i+i, cur_pos_j-j]])[0]>0:
                    sw += 1
                if self.player_map.get_seen_counts([[cur_pos_i-i, cur_pos_j+j]])[0]>0:
                    ne += 1
                if self.player_map.get_seen_counts([[cur_pos_i+i, cur_pos_j+j]])[0]>0:
                    se += 1
        best_diagonal = min(nw, sw, ne, se)
        if best_diagonal == nw:
            if ne > sw:
                return constants.UP
            return constants.LEFT
        elif best_diagonal == sw:
            if se > nw:
                return constants.DOWN
            return constants.LEFT
        elif best_diagonal == ne:
            if nw > se:
                return constants.UP
            return constants.RIGHT
        else:
            if sw > ne:
                return constants.DOWN
            return constants.RIGHT
