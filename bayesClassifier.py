import math


class Classifier:
    def __init__(self, bucketPrefix, testBucketNumber, dataFormat):

        total = 0
        classes = {}
        #non numeric
        counts = {}
        # total numeric
        totals = {}
        #numeric
        numericValues = {}


        self.format = dataFormat.strip().split('\t')

        self.prior = {}
        self.conditional = {}

        # for each of the buckets numbered 1 through 10:
        for i in range(1, 11):

            if i != testBucketNumber:
                filename = "%s-%02i" % (bucketPrefix, i)
                f = open(filename)
                lines = f.readlines()
                f.close()
                for line in lines:
                    fields = line.strip().split(',')
                    vector = []
                    ignore = []
                    nums = []
                    for i in range(len(fields)):
                        if self.format[i] == 'num':
                            nums.append(float(fields[i]))
                        elif self.format[i] == 'attr':
                            vector.append(fields[i])
                        elif self.format[i] == 'comment':
                            ignore.append(fields[i])
                        elif self.format[i] == 'class':
                            category = fields[i]
                    # now process this instance
                    total += 1
                    classes.setdefault(category, 0)
                    counts.setdefault(category, {})
                    totals.setdefault(category, {})
                    numericValues.setdefault(category, {})
                    classes[category] += 1
                    # process non-numeric
                    col = 0
                    for columnValue in vector:
                        col += 1
                        counts[category].setdefault(col, {})
                        counts[category][col].setdefault(columnValue, 0)
                        counts[category][col][columnValue] += 1
                    # process numeric
                    col = 0
                    for columnValue in nums:
                        col += 1
                        totals[category].setdefault(col, 0)
                        totals[category][col] += columnValue
                        numericValues[category].setdefault(col, [])
                        numericValues[category][col].append(columnValue)

        #prior probabilities p(h)
        for (category, count) in classes.items():
            self.prior[category] =count /total

        #conditional probabilities p(h|D)
        for (category, columns) in counts.items():
            self.conditional.setdefault(category, {})
            for (col, valueCounts) in columns.items():
                self.conditional[category].setdefault(col, {})
                for (attrValue, count) in valueCounts.items():
                    self.conditional[category][col][attrValue] = count/ classes[category]

        # now compute mean and sample standard deviation

        self.means = {}
        self.totals = totals
        for (category, columns) in totals.items():
            self.means.setdefault(category, {})
            for (col, cTotal) in columns.items():
                self.means[category][col] = cTotal / classes[category]


        # standard deviation
        self.ssd = {}
        for (category, columns) in numericValues.items():
            self.ssd.setdefault(category, {})
            for (col, values) in columns.items():
                SumOfSquareDifferences = 0
                theMean = self.means[category][col]
                for value in values:
                    SumOfSquareDifferences += (value - theMean) ** 2
                columns[col] = 0
                self.ssd[category][col] = math.sqrt(SumOfSquareDifferences /(classes[category] - 1))

    def testBucket(self, bucketPrefix, bucketNumber):
        filename = "%s-%02i" % (bucketPrefix, bucketNumber)
        f = open(filename)
        lines = f.readlines()
        totals = {}
        f.close()
        loc = 1
        for line in lines:
            loc += 1
            data = line.strip().split(',')
            vector = []
            numV = []
            classInColumn = -1
            for i in range(len(self.format)):
                if self.format[i] == 'num':
                    numV.append(float(data[i]))
                elif self.format[i] == 'attr':
                    vector.append(data[i])
                elif self.format[i] == 'class':
                    classInColumn = i
            theRealClass = data[classInColumn]
            classifiedAs = self.classify(vector, numV)
            totals.setdefault(theRealClass, {})
            totals[theRealClass].setdefault(classifiedAs, 0)
            totals[theRealClass][classifiedAs] += 1
        return totals

    def classify(self, itemVector, numVector):

        results = []
        sqrt2pi = math.sqrt(2 * math.pi)
        for (category, prior) in self.prior.items():
            prob = prior
            col = 1
            for attrValue in itemVector:
                prob = prob * self.conditional[category][col][attrValue]
                col += 1
            col = 1
            for x in numVector:
                mean = self.means[category][col]
                ssd = self.ssd[category][col]
                try:
                    ePart = math.pow(math.e, -(x - mean) ** 2/ (2 * ssd ** 2))
                except ZeroDivisionError:
                    ePart=0.0
                prob = prob * ((1.0 / sqrt2pi * ssd) * ePart)
                col += 1
            results.append((prob, category))
        # return the category with the highest probability
        return (max(results)[1])


def tenfold(bucketPrefix, dataFormat):
    results = {}
    # 10 fold test and get the results for classification
    for i in range(1, 11):
        c = Classifier(bucketPrefix, i, dataFormat)
        t = c.testBucket(bucketPrefix, i)
        for (key, value) in t.items():
            results.setdefault(key, {})
            for (ckey, cvalue) in value.items():
                results[key].setdefault(ckey, 0)
                results[key][ckey] += cvalue


    categories = list(results.keys())
    categories.sort()
    print("\n            Classified as: ")
    header = "             "
    subheader = "               +"

    for category in categories:
        header += "% 10s   " % category
        subheader += "-------+"
    print (header)
    print (subheader)
    total = 0.0
    correct = 0.0
    for key in categories:
        row = " %10s    |" % key
        for ckey in categories:
            if ckey in results[key]:
                count = results[key][ckey]
            else:
                count = 0
            row += " %5i |" % count
            total += count
            if ckey == key:
                correct += count
        print(row)
    print(subheader)
    print("\n%5.3f percent correct" % ((correct * 100) / total))
    print("total of %i instances" % total)


tenfold("Immunotherapy/new", "num\tnum\tnum\tnum\tnum\tnum\tnum\tclass")


